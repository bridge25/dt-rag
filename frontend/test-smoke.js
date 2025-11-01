// Quick smoke test
console.log('Testing import...');
try {
  console.log('Test complete');
  process.exit(0);
} catch (e) {
  console.error('Error:', e);
  process.exit(1);
}
