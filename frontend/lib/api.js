export const GATEWAY_BASE = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://127.0.0.1:8080";

// Distinguishes "the gateway itself is unreachable" (a network-level fetch failure,
// e.g. connection refused) from "the gateway responded but the downstream inference
// call failed" (a resolved response with an error status).
export async function fetchJson(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (networkError) {
    throw { kind: "network", message: networkError.message };
  }
  if (!response.ok) {
    let detail = "";
    try {
      detail = await response.text();
    } catch (_ignored) {
      /* no body to read */
    }
    throw { kind: "http", status: response.status, message: detail };
  }
  return response.json();
}
