/**
 * Custom Jest environment that extends jsdom with Node.js built-in Web APIs.
 * jest-environment-jsdom's VM sandbox doesn't include Node 24 globals like
 * fetch, Request, Response, ReadableStream, MessagePort, etc.
 * This environment copies them from the Node.js process into the sandbox.
 */
import JSDOMEnvironment from "jest-environment-jsdom";
import type { JestEnvironmentConfig, EnvironmentContext } from "@jest/environment";

export default class FixedJSDOMEnvironment extends JSDOMEnvironment {
  constructor(config: JestEnvironmentConfig, context: EnvironmentContext) {
    super(config, context);

    // Node 24 built-in Web API globals to expose in jsdom sandbox
    const webApiGlobals = [
      "TextEncoder",
      "TextDecoder",
      "ReadableStream",
      "WritableStream",
      "TransformStream",
      "Blob",
      "MessageChannel",
      "MessagePort",
      "MessageEvent",
      "fetch",
      "Request",
      "Response",
      "Headers",
      "FormData",
      "AbortController",
      "AbortSignal",
      "structuredClone",
      "BroadcastChannel",
    ] as const;

    for (const name of webApiGlobals) {
      const nodeGlobal = (globalThis as Record<string, unknown>)[name];
      const sandboxGlobal = (this.global as Record<string, unknown>)[name];
      if (nodeGlobal !== undefined && sandboxGlobal === undefined) {
        (this.global as Record<string, unknown>)[name] = nodeGlobal;
      }
    }
  }
}
