// Builds the plant drawing off the main thread: settling the depth order takes a second or two.
import { buildPlant } from "./plant.mjs";

self.onmessage = ({ data: { id, spec, size } }) => {
  try {
    const { svg, calls, dims, capped, count } = buildPlant(spec, size);
    self.postMessage({ id, svg, calls, dims, capped, count });
  } catch (err) {
    self.postMessage({ id, error: String(err && err.stack || err) });
  }
};
