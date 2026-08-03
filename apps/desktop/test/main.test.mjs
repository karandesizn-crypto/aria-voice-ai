import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { resolveAppUrl } = require("../app-url.js");

test("desktop resolves app url from env", () => {
  assert.equal(
    resolveAppUrl({ DESKTOP_APP_URL: "http://localhost:3000" }),
    "http://localhost:3000",
  );
  assert.equal(resolveAppUrl({}), "http://localhost:3000");
});
