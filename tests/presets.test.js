// Regression check: the headline numbers each preset produced when the bench was handed over.
// If you change the physics on purpose, update the expected values here and say why in the commit.
const test = require("node:test");
const assert = require("node:assert");
const B = require("../physics.js");

const EXPECTED = {
  //               g/s    °C     kW     COP
  rental:         [78.0,  0.8,  2.29, 0.098],
  workshopVortex: [3.2,  19.0,  0.04, 0.021],
  workshopBurst:  [19.5,  0.7,  0.58, 0.070],
  scuba:          [3.2,  -7.3,  0.12, 0.027],
  junior:         [2.0, -79.8,  0.22, 0.101],
};

for (const [key, [m, T, cool, cop]] of Object.entries(EXPECTED)) {
  test(`preset ${key}`, () => {
    B.loadPreset(key);
    const r = B.compute(B.getState());
    assert.ok(Math.abs(r.m * 1000 - m) < 0.15, `mass flow ${(r.m * 1000).toFixed(2)} g/s, expected ${m}`);
    assert.ok(Math.abs(r.T - T) < 0.15, `outlet ${r.T.toFixed(2)} °C, expected ${T}`);
    assert.ok(Math.abs(r.cool / 1000 - cool) < 0.01, `cooling ${(r.cool / 1000).toFixed(3)} kW, expected ${cool}`);
    assert.ok(Math.abs(r.cop - cop) < 0.002, `COP ${r.cop.toFixed(4)}, expected ${cop}`);
  });
}

test("Joule-Thomson drop from 200 to 6.3 bar(g) is about 30 K", () => {
  const d = B.jtDrop(200 + B.PA, 6.3 + B.PA);
  assert.ok(d > 28 && d < 33, `got ${d.toFixed(1)} K`);
});
