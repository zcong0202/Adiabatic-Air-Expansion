const fs=require('node:fs'),assert=require('node:assert/strict'),Core=require('../src/core.js');
const a=Core.parseHex(fs.readFileSync('/tmp/aa-custom-firmware/aa_hold_controller.hex','utf8'));
const b=Core.parseHex(fs.readFileSync('/tmp/aa-custom-build/aa_hold_controller.ino.hex','utf8'));
assert.deepEqual(a,b);console.log('PASS: browser-exported HEX exactly equals Arduino compiler output for exported 12.3 s LOW-trigger source.');
