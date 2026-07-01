const { execSync } = require('child_process');
process.chdir('D:/Project/Github/PlantOS/frontend');
console.log('Building...');
execSync('npm run build', { stdio: 'inherit' });
console.log('Build complete');
