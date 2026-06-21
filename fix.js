const fs = require('fs');
const path = require('path');

const directory = '.';

const replacements = {
    "â€”": "—",
    "â†’": "→",
    "â† ": "←",
    "COâ‚‚": "CO₂",
    "1.5Â°C": "1.5°C",
    "Â·": "·",
    "Â©": "©",
    "ðŸŒ ": "🌍",
    "ðŸ“Š": "📊",
    "âœ✨": "✨",
    "âœ¨": "✨",
    "ðŸ”’": "🔒",
    "ðŸ” ": "🔍",
    "âœ…": "✅",
    "âš ï¸ ": "⚠️",
    "â”€": "─",
    "â”œ": "├",
    "â””": "└",
    "â”‚": "│",
    "â–º": "►",
    "â–¼": "▼",
    "â€œ": "“",
    "â€ ": "”",
    "â€™": "’",
    "â€˜": "‘",
};

function walkAndFix(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        if (fullPath.includes('node_modules') || fullPath.includes('.git') || fullPath.includes('.venv') || fullPath.includes('coverage')) {
            continue;
        }
        
        const stat = fs.statSync(fullPath);
        if (stat.isDirectory()) {
            walkAndFix(fullPath);
        } else if (stat.isFile() && /\.(tsx|ts|css|html|md|json|yml|example|local)$/.test(file)) {
            let content = fs.readFileSync(fullPath, 'utf-8');
            let fixedContent = content;
            
            for (const [bad, good] of Object.entries(replacements)) {
                fixedContent = fixedContent.split(bad).join(good);
            }
            
            if (fixedContent !== content) {
                fs.writeFileSync(fullPath, fixedContent, 'utf-8');
                console.log('Fixed:', fullPath);
            }
        }
    }
}

walkAndFix(directory);
