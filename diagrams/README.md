# Demo diagram

`demo-setup.html` explains the current AM0701 friction-brake demo.

- `demo-setup.mmd`: grouped flowchart source.
- `demo-setup.svg` / `.png`: rendered presentation diagrams.
- `demo-setup.excalidraw`: editable boxes, text and arrows. Open with Excalidraw, File → Open.

The Excalidraw conversion omits section wrappers and connects valve → motor → collector directly. The converter cannot resolve these subgraphs. It is not an embedded image.

Render SVG/PNG in a fresh diagram-render page before converting Excalidraw. The converter changes Mermaid state. A later SVG render in the same page can contain malformed foreignObject markup.

Current diagram is a functional architecture. Exact shaft/port connections, pressure protection, exhaust collection, brake ratings and actual motor flow remain unverified. No fitted CAD or pressure-system qualification is implied.
