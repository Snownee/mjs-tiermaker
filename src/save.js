import ByteBuffer from "byte-buffer";
import Pako from "pako";
import { INIT_TIERS } from "./utils/constants";

/**
 * Data structure example:
 * {
 *   title: 'My Tier List',
 *   subtitle: 'Best characters',
 *   tiers: [
 *     {
 *       name: 'S',
 *       color: '#ff7f7f',
 *       items: [0, 1, 2] // Character IDs
 *     }
 *   ]
 * }
 */

/**
 * Save tier list data to a compressed base64 string
 * @param {Object} data - The data to save
 * @returns {string} Compressed and encoded data string
 */
export const save = (data) => {
  // Create a byte buffer for efficient data storage
  const b = new ByteBuffer(1024, ByteBuffer.BIG_ENDIAN, true);

  // Write title and subtitle as null-terminated strings
  b.writeCString(data.title || "");
  b.writeCString(data.subtitle || "");

  let useDefaultTiers = false;
  if (data.tiers.length === INIT_TIERS.length) {
    useDefaultTiers = data.tiers.every(
      (tier, i) =>
        tier.name === INIT_TIERS[i].name && tier.color === INIT_TIERS[i].color,
    );
  }

  // Write number of tiers
  b.writeUnsignedByte(useDefaultTiers ? 0 : data.tiers.length);

  // Write each tier's data
  for (const tier of data.tiers) {
    if (!useDefaultTiers) {
      b.writeCString(tier.name);

      // Handle color - remove # if present
      let color = tier.color;
      if (color.startsWith("#")) {
        color = color.slice(1);
      }
      b.writeCString(color);
    }

    // Write number of items in this tier
    b.writeUnsignedShort(tier.items.length);

    // Write each item ID
    for (const item of tier.items) {
      b.writeUnsignedShort(item);
    }
  }

  // Get raw bytes and compress with Pako
  let raw = b.clip(0, b.index).raw;
  raw = Pako.deflate(raw);

  // Convert to base64 and remove padding
  const base64String = btoa(String.fromCharCode(...raw));
  return "0" + base64String.replaceAll("=", "");
};

/**
 * Load tier list data from a compressed base64 string
 * @param {string} data - The encoded data string
 * @returns {Object} Decoded data object or error object
 */
export const load = (data) => {
  // Check version (currently only "0" is supported)
  const version = data.charAt(0);
  if (version !== "0") {
    return { error: 1 }; // Unsupported version
  }

  // Remove version prefix
  data = data.slice(1);

  // Find and remove any trailing parameters
  const i = data.indexOf("&");
  if (i !== -1) {
    data = data.slice(0, i);
  }

  // Add back missing base64 padding
  const missingPadding = (4 - (data.length % 4)) % 4;
  data += "=".repeat(missingPadding);

  // Decode base64 to binary
  const binary = atob(data);
  let array = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    array[i] = binary.charCodeAt(i);
  }

  // Decompress with Pako
  try {
    array = Pako.inflate(array);
  } catch (err) {
    return { error: 2 }; // Decompression failed
  }

  // Parse binary data
  const b = new ByteBuffer(array, ByteBuffer.BIG_ENDIAN, true);

  const title = b.readCString();
  const subtitle = b.readCString();
  const tierCount = b.readUnsignedByte();

  const tiers = [];
  if (tierCount === 0) {
    // Use default tiers
    for (const defaultTier of INIT_TIERS) {
      const itemCount = b.readUnsignedShort();
      const items = new Set();
      for (let j = 0; j < itemCount; j++) {
        items.add(b.readUnsignedShort());
      }
      tiers.push({
        name: defaultTier.name,
        color: defaultTier.color,
        items: Array.from(items),
      });
    }
  } else {
    for (let i = 0; i < tierCount; i++) {
      const name = b.readCString();
      let color = b.readCString();

      // Add # prefix if it's a 6-digit hex color
      if (/^[0-9a-fA-F]{6}$/.test(color)) {
        color = "#" + color;
      }

      // Read items as a Set to handle duplicates
      const items = new Set();
      const itemCount = b.readUnsignedShort();
      for (let j = 0; j < itemCount; j++) {
        items.add(b.readUnsignedShort());
      }

      tiers.push({ name, color, items: Array.from(items) });
    }
  }

  return { title, subtitle, tiers };
};
