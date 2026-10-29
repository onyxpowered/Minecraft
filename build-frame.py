#!/usr/bin/env python3
"""Writes frame/qr-frame.html: the Status link and QR popup of the loading cover, as a page of its own.

The client shows it in a transparent iframe over the cover's bottom-right corner. It is deployed to a different site than the client
(onyxpowered.github.io), so the browser can give it its own process: a press on Status is then answered even while the game's
own page is busy starting. Run after changing the cover in Minecraft.html, then push frame/qr-frame.html to the `pages` branch (GitHub Pages).
"""
import os, re
here = os.path.dirname(os.path.abspath(__file__))
d = open(os.path.join(here, 'Minecraft.html'), 'rb').read().decode('latin1')
i = d.index("coverElement = ACCR('") + len("coverElement = ACCR('"); cover = d[i:d.index("');\n", i)]
foot = cover[cover.index('<div class="ld-foot ld-foot-r">'):cover.index('<iframe')]
foot = foot[:foot.rindex('</div>')]
css_at = d.index('<style>#brand-load'); css = d[css_at + 7:d.index('</style>', css_at)]
rules = [l for l in css.split('\n') if re.search(r'\.ld-foot(?!-l)|\.ld-ink|\.ld-status|\.ld-qr|prefers-reduced-motion', l) and '.ld-logo' not in l and 'ld-framed' not in l]
page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Status</title>
<style>
html, body { margin: 0; height: 100%; overflow: hidden; background: transparent; color-scheme: normal; }
#brand-load { position: fixed; inset: 0; --ease: cubic-bezier(.22, 1, .36, 1); }
#brand-load .ld-foot { transition: opacity .35s ease; }
''' + '\n'.join(rules) + '''
</style></head><body>
<div id="brand-load">''' + foot + '''</div>
<script>
// The client page (the parent) says "arc-in" when its cover fades in and "arc-close" when something outside is pressed; this page says
// "arc-ready" once loaded and "arc-shown" when it is visible, after which the client hides its own copy of this corner.
(function () {
  var root = document.getElementById("brand-load"), foot = root.querySelector(".ld-foot-r"), link = root.querySelector(".ld-status");
  var setOpen = function (on) {
    foot.classList.toggle("ld-open", on); link.setAttribute("aria-expanded", on ? "true" : "false");
    try { sessionStorage.setItem("arc:qr", on ? String(Date.now()) : "0"); } catch (e) {}      // the client reloads this page when it swaps builds
  };
  link.addEventListener("pointerdown", function (e) { if (e.button) return; e.preventDefault(); setOpen(!foot.classList.contains("ld-open")); });
  link.addEventListener("click", function (e) { e.preventDefault(); });
  document.addEventListener("pointerdown", function (e) { if (!foot.contains(e.target)) setOpen(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") setOpen(false); });
  try { if (Date.now() - Number(sessionStorage.getItem("arc:qr")) < 8000) foot.classList.add("ld-open"); } catch (e) {}     // only across a build swap, not a later visit
  window.addEventListener("message", function (e) {
    if (e.source !== parent) return;
    if (e.data === "arc-in") { root.classList.add("ld-in"); parent.postMessage("arc-shown", "*"); }
    else if (e.data === "arc-close") setOpen(false);
  });
  parent.postMessage("arc-ready", "*");
})();
</script></body></html>
'''
os.makedirs(os.path.join(here, 'frame'), exist_ok=True)
open(os.path.join(here, 'frame', 'qr-frame.html'), 'w', encoding='utf-8').write(page.encode('latin1').decode('utf-8', 'ignore') if False else page)
print(len(page), 'bytes ->', 'frame/qr-frame.html')
