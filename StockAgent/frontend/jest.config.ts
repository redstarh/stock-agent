import type { Config } from "jest";
import nextJest from "next/jest.js";

const createJestConfig = nextJest({
  dir: "./",
});

const config: Config = {
  setupFilesAfterEnv: ["<rootDir>/tests/setup.ts"],
  testEnvironment: "<rootDir>/tests/jest-env-jsdom.ts",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  testPathIgnorePatterns: ["<rootDir>/node_modules/", "<rootDir>/.next/"],
  collectCoverageFrom: ["src/**/*.{ts,tsx}", "!src/**/*.d.ts"],
  coverageThreshold: {
    global: {
      lines: 70,
    },
  },
};

// next/jest overrides transformIgnorePatterns, so we patch it after resolution
const jestConfig = async () => {
  const resolved = await createJestConfig(config)();
  resolved.transformIgnorePatterns = [
    "node_modules/(?!(msw|@mswjs|until-async)/)",
  ];
  return resolved;
};

export default jestConfig;
