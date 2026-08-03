function resolveAppUrl(env = process.env) {
  return env.DESKTOP_APP_URL || env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
}

module.exports = { resolveAppUrl };
