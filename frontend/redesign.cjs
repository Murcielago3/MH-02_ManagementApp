const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'src');

const replacements = [
  { regex: /#1a1a2e/gi, replace: 'var(--color-primary)' },
  { regex: /#0d9488/gi, replace: 'var(--color-primary)' },
  { regex: /#287475/gi, replace: 'var(--color-primary)' },
  
  { regex: /#1c1b1d/gi, replace: 'var(--color-on-surface)' },
  { regex: /#0f172a/gi, replace: 'var(--color-on-surface)' },
  
  { regex: /#334155/gi, replace: 'var(--color-on-surface-variant)' },
  { regex: /#47464c/gi, replace: 'var(--color-on-surface-variant)' },
  { regex: /#475569/gi, replace: 'var(--color-on-surface-variant)' },
  { regex: /#64748b/gi, replace: 'var(--color-on-surface-variant)' },
  { regex: /#78767d/gi, replace: 'var(--color-on-surface-variant)' },
  { regex: /#83829b/gi, replace: 'var(--color-on-surface-variant)' },
  { regex: /#94a3b8/gi, replace: 'var(--color-outline)' },
  
  { regex: /#f6f2f4/gi, replace: 'var(--color-surface-container)' },
  { regex: /#f1f5f9/gi, replace: 'var(--color-surface-container)' },
  { regex: /#f1edef/gi, replace: 'var(--color-surface-container)' },
  
  { regex: /#ebe7e9/gi, replace: 'var(--color-surface-container-high)' },
  { regex: /#e2e8f0/gi, replace: 'var(--color-surface-container-high)' },
  
  { regex: /#c8c5cd/gi, replace: 'var(--color-outline)' },
  { regex: /#cbd5e1/gi, replace: 'var(--color-outline)' },
  
  { regex: /#fcf8fa/gi, replace: 'var(--color-background)' },
  { regex: /#f8f9fa/gi, replace: 'var(--color-background)' },
  { regex: /#f8fafc/gi, replace: 'var(--color-background)' },
  
  { regex: /'Integral CF', sans-serif/gi, replace: 'var(--font-display)' },
  { regex: /Inter, sans-serif/gi, replace: 'var(--font-body)' },
  
  { regex: /border-radius:\s*4px/g, replace: 'border-radius: var(--radius)' },
  { regex: /border-radius:\s*6px/g, replace: 'border-radius: var(--radius-lg)' },
  { regex: /border-radius:\s*8px/g, replace: 'border-radius: var(--radius-lg)' },
  { regex: /border-radius:\s*10px/g, replace: 'border-radius: var(--radius-lg)' },
  { regex: /border-radius:\s*12px/g, replace: 'border-radius: var(--radius-lg)' },
];

function processFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let changed = false;
  
  for (const r of replacements) {
    if (r.regex.test(content)) {
      content = content.replace(r.regex, r.replace);
      changed = true;
    }
  }
  
  if (changed) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log('Updated ' + filePath);
  }
}

function traverseDir(dir) {
  fs.readdirSync(dir).forEach(file => {
    let fullPath = path.join(dir, file);
    if (fs.lstatSync(fullPath).isDirectory()) {
      traverseDir(fullPath);
    } else if (fullPath.endsWith('.vue')) {
      processFile(fullPath);
    }
  });
}

traverseDir(srcDir);
console.log('Done.');
