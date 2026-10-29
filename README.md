# Minecraft

The Minecraft client for Arc, as one HTML file.

- `Minecraft.html` is the client.
- `Minecraft-Auto.html` (made by `build.py`, not stored here) is the file to hand out. It carries the build that was current when it was made and, on every open, checks this repository through jsDelivr for a newer release. A newer build is downloaded in the background, checked against its SHA-256, kept in the browser, and used the next time the page is opened.

## Releasing

```
python3 build.py 1.0.1        # builds Minecraft-Auto.html, dist/ and version.json from Minecraft.html
git add -A && git commit -m "1.0.1"
git tag v1.0.1 && git push && git push --tags
```

jsDelivr will not serve a GitHub file over 20 MB, so the release is stored as `dist/part-N.bin`, a gzip of the whole page cut into 12 MB pieces. `version.json` lists the pieces and their checksum.
