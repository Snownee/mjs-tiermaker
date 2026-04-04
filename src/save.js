import ByteBuffer from 'byte-buffer';
import Pako from 'pako';

/*
const example_data = {
    title: '',
    subtitle: '',
    tiers: [
        {
            name: '',
            color: '',
            items: [0, 1, 2]
        },
        {
            name: '',
            color: '',
            items: [5, 3]
        }
    ]
}
 */

export const save = (data) => {
    // console.log(data);
    const b = new ByteBuffer(1024, ByteBuffer.BIG_ENDIAN, true);

    b.writeCString(data.title || '')
    b.writeCString(data.subtitle || '')
    b.writeUnsignedByte(data.tiers.length)
    for (const tier of data.tiers) {
        b.writeCString(tier.name)
        let color = tier.color
        if (color.startsWith('#')) {
            color = color.slice(1)
        }
        b.writeCString(color)
        b.writeUnsignedShort(tier.items.length)
        for (const item of tier.items) {
            b.writeUnsignedShort(item)
        }
    }

    let raw = b.clip(0, b.index).raw
    // console.log(raw);
    // console.log("before: " + raw.length);
    raw = Pako.deflate(raw)
    // console.log(raw);
    // console.log("after: " + raw.length);

    const base64String = btoa(String.fromCharCode(...raw));
    // console.log(base64String);
    return "0" + base64String
}

export const load = (data) => {
    const version = data.charAt(0)
    if (version !== "0") {
        return { error: 1 }
    }
    const binary = atob(data.slice(1));
    let array = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        array[i] = binary.charCodeAt(i);
    }

    try {
        array = Pako.inflate(array);
    } catch (err) {
        return { error: 2 }
    }

    const b = new ByteBuffer(array, ByteBuffer.BIG_ENDIAN, true);
    const title = b.readCString()
    
    const subtitle = b.readCString()
    const tierCount = b.readUnsignedByte()
    const tiers = []
    for (let i = 0; i < tierCount; i++) {
        const name = b.readCString()
        let color = b.readCString()
        if (/^[0-9a-fA-F]{6}$/.test(color)) {
            color = '#' + color
        }
        const items = new Set()
        const itemCount = b.readUnsignedShort()
        for (let j = 0; j < itemCount; j++) {
            items.add(b.readUnsignedShort())
        }
        tiers.push({ name, color, items: Array.from(items) })
    }
    return { title, subtitle, tiers }
}