// Minecraft auto-updater. build.py injects this at the very top of <head>, with the version of the page it sits in filled in.
//
// Every open, in the background: ask jsDelivr whether the repo has a newer release; if so, download it, check it, and keep it
// for the next open. (Minecraft-Auto.html, the launcher around this page, is what loads a stored build in place of its own.)
(function () {
  var REPO = "onyxpowered/Minecraft", BUILD = "__BUILD__", FLAG = "arc:update", DB = "arc-update";
  var CDN = "https://cdn.jsdelivr.net/gh/" + REPO;
  var nativeFetch = window.fetch ? window.fetch.bind(window) : null;   // the game later replaces fetch with a filtered one

  var cmp = function (a, b) {
    a = String(a).split("."); b = String(b).split(".");
    for (var i = 0; i < 3; i++) { var d = (+a[i] || 0) - (+b[i] || 0); if (d) return d; }
    return 0;
  };
  var store = function (mode, fn) {
    return new Promise(function (resolve, reject) {
      var open = indexedDB.open(DB, 1);
      open.onupgradeneeded = function () { open.result.createObjectStore("b"); };
      open.onerror = function () { reject(open.error); };
      open.onsuccess = function () {
        var db = open.result, tx = db.transaction("b", mode), req = fn(tx.objectStore("b"));
        tx.oncomplete = function () { db.close(); resolve(req && req.result); };
        tx.onerror = tx.onabort = function () { db.close(); reject(tx.error); };
      };
    });
  };

  // Which build is stored for the next open (the launcher around this page loads it in place of the one it carries).
  var ready = null;
  try { ready = localStorage.getItem(FLAG); } catch (e) {}

  if (!nativeFetch || !window.indexedDB || !window.DecompressionStream || !window.Blob) return;
  var getJSON = function (url) { return nativeFetch(url, { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error(url + " " + r.status); return r.json(); }); };

  // Runs once the page has had time to load, so the check never competes with the game starting.
  var check = function () {
    getJSON(CDN + "@latest/version.json").then(function (found) {
      var latest = found && found.version;
      if (!latest || cmp(latest, BUILD) <= 0 || (ready && cmp(latest, ready) <= 0)) return;
      return getJSON(CDN + "@" + latest + "/version.json").then(function (info) {
        var parts = [], n = 0;
        var next = function (i) {
          if (i >= info.parts) return Promise.resolve();
          return nativeFetch(CDN + "@" + latest + "/dist/part-" + i + ".bin").then(function (r) {
            if (!r.ok) throw new Error("part " + i + " " + r.status);
            return r.arrayBuffer();
          }).then(function (buf) { parts.push(buf); n += buf.byteLength; return next(i + 1); });
        };
        return next(0).then(function () {
          if (n !== info.gzBytes) throw new Error("size mismatch");
          var gz = new Blob(parts);
          var verify = window.crypto && crypto.subtle
            ? gz.arrayBuffer().then(function (b) { return crypto.subtle.digest("SHA-256", b); }).then(function (h) {
                var hex = Array.prototype.map.call(new Uint8Array(h), function (x) { return ("0" + x.toString(16)).slice(-2); }).join("");
                if (hex !== info.gzSha256) throw new Error("checksum mismatch");
              })
            : Promise.resolve();
          return verify.then(function () {
            return new Response(gz.stream().pipeThrough(new DecompressionStream("gzip"))).blob();
          });
        }).then(function (html) {
          return store("readwrite", function (s) { return s.put({ version: latest, blob: html }, "build"); });
        }).then(function () {
          try { localStorage.setItem(FLAG, latest); } catch (e) {}
          if (window.console) console.log("Minecraft " + latest + " is ready; it loads the next time you open this page.");
        });
      });
    }).catch(function (e) { if (window.console) console.log("Minecraft update check: " + (e && e.message || e)); });
  };
  window.addEventListener("load", function () { setTimeout(check, 15000); });
})();
