import * as fs from 'node:fs';

const namespace = process.argv[2]
const sourceFolder = `src_${namespace}`
const targetFolder = `src`

const config = JSON.parse(fs.readFileSync(`${sourceFolder}/config.json`, 'utf-8'))
if (!config) {
    console.error(`Invalid ${sourceFolder}/config.json`);
    process.exit(1);
}

for (const file of config.delete_files || []) {
    const targetPath = `${targetFolder}/${file}`;
    if (fs.existsSync(targetPath)) {
        fs.rmSync(targetPath, { recursive: true, force: true });
        console.log(`Deleted ${targetPath}`);
    } else {
        console.warn(`File ${targetPath} does not exist, skipping deletion.`);
    }
}

const files = fs.readdirSync(sourceFolder);
for (const file of files) {
    if (file === 'config.json') {
        continue;
    }
    const sourcePath = `${sourceFolder}/${file}`;
    const targetPath = `${targetFolder}/${file}`;
    fs.cpSync(sourcePath, targetPath, { recursive: true });
    console.log(`Copied ${sourcePath} to ${targetPath}`);
}

console.log('All files processed successfully.');