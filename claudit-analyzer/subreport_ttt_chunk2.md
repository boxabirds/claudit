# Subreport 2/13: Ttt

This conversation chunk details a significant period of development, primarily focused on setting up the React frontend, integrating the Evolu local-first database, and establishing a robust testing pipeline. It highlights a recurring pattern of initial implementation based on potentially outdated documentation, followed by extensive debugging and API re-discovery.

### 1. Significant Decisions

*   **Adoption of `main.tsx` as React Entry Point (15:42:32Z):** Decided to use `main.tsx` for React rendering instead of the initial `index.ts`.
*   **Proactive Implementation of Task 1-2 Components (15:42:58Z):** Despite Task 1-2 being marked "Proposed," the assistant decided to create `vite.config.ts` and `index.html` as they were necessary for the current task (routing) to function.
*   **Creation of Stub Files for Future Tasks (15:43:20Z):** To resolve immediate compilation errors, the assistant created placeholder files (`evolu-react.tsx`, `schema.ts`, `useChats.ts`, `useMessages.ts`) for Task 1-3, acknowledging they would be replaced later.
*   **Formalizing Task Sequencing and Status Checks (15:51:17Z):** The user explicitly requested a new guideline in `CLAUDE.md` to ensure the AI agent checks the status of preceding tasks before starting a new one, and asks for user direction if tasks are incomplete. This is a critical process improvement.
*   **Comprehensive Task Status Audit (15:54:39Z):** Initiated a detailed audit of all PBI-1 tasks to synchronize documented status with actual implementation.
*   **Deep Dive into Evolu API (19:11:49Z, 19:18:11Z):** Faced with persistent and complex TypeScript errors related to Evolu, the assistant made a crucial decision to perform extensive internal investigation of the `@evolu/common` and `@evolu/react` packages to understand the correct API patterns for the preview version.
*   **Schema Adjustment for Ownership (19:24:22Z, 19:26:44Z):** After discovering Evolu doesn't have a built-in `createdBy` field at the record level, it was decided to explicitly add an `ownerId` field to the `message` table in the schema and populate it with `useAppOwner().id`.
*   **Switching Test Relay Implementation (20:05:13Z):** Due to persistent "Cannot perform I/O on behalf of a different request" errors with the Cloudflare Workers relay in local testing, it was decided to replace it with a simpler Node.js WebSocket server (`test-relay.cjs`).
*   **Refactoring Test Naming and Execution (20:05:13Z):** Renamed Playwright test files from `.spec.ts` to `.test.playwright.ts` and adjusted `package.json` scripts to ensure `bun test` (Bun's internal runner) doesn't conflict with Playwright tests, and `bun run test` correctly executes Playwright.
*   **Improving Test Accuracy (20:05:13Z):** Modified a Playwright test that was "swallowing failures" (logging a "known issue" instead of failing) to accurately reflect expected behavior and pass/fail.

### 2. Mistakes

*   **Incorrect Assumption of Main React Entry File (15:42:27Z):** Initially assumed `index.ts` was the main React entry point, leading to a need to create `main.tsx`.
*   **Out-of-Sync Task Status (15:42:58Z, 15:57:17Z):** Several tasks (especially 1-2, 1-3, 1-4) were prematurely marked as "Done" or "Proposed" in documentation, while critical dependencies or core implementations were missing. This led to significant rework and debugging.
*   **Misunderstanding Evolu API (15:43:15Z, 19:11:43Z, 19:18:06Z):** This was the most prominent and recurring mistake.
    *   Initial attempts used outdated API patterns (`database()`, `table()`, `cast()`, `safeParse()`, `result.row`) that were not present in the Evolu preview version.
    *   Incorrectly assumed `createdAt` should be manually added to the schema.
    *   Misunderstood the return type of `useQuery` (expected object with `rows` property, got array directly).
    *   Misunderstood the `useOwner` vs `useAppOwner` distinction and the `OwnerId` vs `UserId` type mismatch.
    *   Misunderstood how `isDeleted` should be set (expected `SqliteBoolean` type, but `true` boolean is sufficient).
*   **Incomplete Dependency Installation (15:56:22Z, 15:56:31Z):** Despite previous attempts, core React, Vite, and Evolu runtime dependencies were not fully installed, leading to compilation and runtime errors.
*   **Incorrect `bunfig.toml` Syntax (20:05:13Z):** Initial attempt to configure `bunfig.toml` to exclude Playwright tests had a syntax error (`preload = []` instead of `exclude = []`).
*   **Misuse of `bun test` vs `bun run test` (20:05:13Z):** Repeatedly confused `bun test` (Bun's internal test runner) with `bun run test` (executing the `test` script defined in `package.json`), leading to "no tests found" errors.
*   **"Swallowing" Test Failures (20:05:13Z):** A test was designed to `console.log` a "Known issue" instead of failing, masking a real problem and providing misleading test results.

### 3. Milestones

*   **Initial CSS Styling (15:42:02Z):** `index.css` created with comprehensive styling.
*   **Component and Page Export Indexes (15:42:10Z, 15:42:16Z):** `src/components/index.ts` and `src/pages/index.ts` created.
*   **React Entry Point (`main.tsx`) Created (15:42:34Z):** Essential file for React application bootstrapping.
*   **Vite Configuration and HTML Entry Point (15:43:02Z, 15:43:08Z):** `vite.config.ts` and `index.html` created, enabling Vite build tooling.
*   **Evolu Stub Files Created (15:43:29Z - 15:43:49Z):** Initial placeholder files for Evolu integration (`evolu-react.tsx`, `schema.ts`, `useChats.ts`, `useMessages.ts`).
*   **Initial TypeScript Errors Resolved (15:45:32Z):** After several fixes, the project compiled without errors for the first time.
*   **Task 1-4 Marked as Done (15:48:12Z):** Project structure and routing considered complete in documentation.
*   **New Task Sequencing Guideline in `CLAUDE.md` (15:51:34Z):** A new process for managing task dependencies was added.
*   **React and Vite Dependencies Installed (15:58:17Z, 15:58:24Z):** Core frontend libraries were finally installed.
*   **Vite Scripts Configured (15:58:33Z):** `package.json` updated with proper Vite commands.
*   **Dev Server Successfully Started (15:58:53Z):** Confirmed the React development server could run.
*   **Task 1-2 Marked as Done (16:42:18Z):** React 19 and Vite setup officially completed.
*   **Evolu Core Packages and `nanoid` Installed (19:09:44Z, 19:09:49Z):** Essential Evolu libraries and `nanoid` were installed.
*   **Evolu Schema Defined (19:10:11Z):** `src/schema.ts` updated with the correct Evolu schema structure.
*   **Evolu Instance and React Integration (19:10:23Z, 19:10:35Z):** `src/lib/evolu.ts` and `src/lib/evolu-react.tsx` were created/updated.
*   **Evolu Hooks Implemented (19:10:46Z, 19:10:55Z):** `useChats.ts` and `useMessages.ts` were updated with Evolu logic.
*   **`.env.local` Created (19:11:24Z):** Environment variable file for Evolu sync URL.
*   **Task 1-3 Marked as Done (19:42:53Z):** Evolu integration officially completed.
*   **Logbook Created and Documented (19:42:48Z):** `docs/logbook.md` was created with a detailed entry on Evolu integration challenges.
*   **Playwright Test Discovery Confirmed (20:05:13Z):** `bunx playwright test --list` successfully listed all tests.
*   **Node.js Test Relay Implemented (20:05:13Z):** A functional local WebSocket server for testing was created.
*   **All Playwright Tests Passing (20:05:13Z):** After numerous fixes, all 16 E2E tests passed cleanly.
*   **Task 1-7 Marked as Done (20:05:13Z):** Basic chat functionality officially completed.
*   **Task 1-8 Detail Document Created (20:05:13Z):** Plan for user identity system outlined.
*   **Schema Updated for User Identity (20:05:13Z):** `User` table and `authorDisplayName` added to `Message` table.
*   **User Management Hooks Created (20:05:13Z):** `useUser.ts` implemented.
*   **Avatar Configuration and Components (20:05:13Z):** `avatars.ts`, `ProfileSetupModal.tsx`, `UserAvatar.tsx` created.
*   **Profile Setup Integrated into App (20:05:13Z):** `App.tsx` updated to show profile modal for new users.
*   **Chat Page Updated for User Profiles (20:05:13Z):** `ChatPage.tsx` updated to display user avatars and names.

### 4. Timeline

*   **15:42:02Z - 15:42:34Z:** Initial frontend setup: `index.css`, component/page index files, `main.tsx` (React entry point).
*   **15:42:39Z - 15:43:08Z:** Realization that `vite.config.ts` and `index.html` were missing (from Task 1-2), and their creation.
*   **15:43:13Z - 15:45:32Z:** First major debugging cycle: Numerous TypeScript errors due to missing Evolu stubs, incorrect type imports, and missing `nanoid`. Creation of Evolu stub files, fixing type imports, installing missing React types, and temporarily removing `nanoid` usage.
*   **15:45:37Z - 15:48:44Z:** Cleanup of old `index.ts`, attempt to run dev server (failed due to unconfigured `dev` script), and marking Task 1-4 as "Done" in documentation.
*   **15:51:17Z - 15:54:39Z:** User requests improved task sequencing and a "stock-take" of task statuses.
*   **15:54:39Z - 15:57:31Z:** Comprehensive audit of task statuses, revealing critical missing dependencies (React, Vite, Evolu runtime packages) and significant misalignment between documented and actual progress. Project declared "non-functional."
*   **15:58:04Z - 16:42:47Z:** Focused effort to "finish Task 1-2": Installing React, React DOM, Vite, and its plugin. Updating `package.json` scripts. Verifying dev server starts. Task 1-2 marked as "Done."
*   **19:09:17Z - 19:11:31Z:** Start of "finish Task 1-3": Installing Evolu packages and `nanoid`. Initial implementation of Evolu schema, instance, and hooks. First typecheck reveals major API mismatches.
*   **19:11:35Z - 19:13:51Z:** First deep dive into Evolu API: Extensive investigation of `@evolu/common` exports and documentation to understand correct schema definition, data types (`DateIsoString`), and method calls (`.from()`, `.value`, `insert()`, `update()`).
*   **19:14:00Z - 19:21:32Z:** Applying Evolu API fixes: Updating `schema.ts`, `useChats.ts`, `useMessages.ts`, `evolu-react.tsx`, `Layout.tsx`, `MessageList.tsx`. Second typecheck reveals new errors related to `createdBy` and `OwnerId` types.
*   **19:21:38Z - 19:26:44Z:** Second deep dive into Evolu API (ownership): Investigation of Evolu's ownership model, confirming no built-in `createdBy` field, and identifying `OwnerId` as the correct type from `useAppOwner()`.
*   **19:26:48Z - 19:27:22Z:** Applying ownership fixes: Updating `schema.ts` to use `ownerId`, and updating `useMessages.ts` and `MessageList.tsx` to use `message.ownerId`. All TypeScript errors resolved.
*   **19:27:30Z - 19:43:26Z:** Attempting to run dev server (timed out). User requests logbook entry about the "palaver." Creation of `docs/logbook.md` with detailed root cause analysis of Evolu integration issues. Task 1-3 marked as "Done."
*   **20:05:13Z (Continuation):** User provides summary of previous session, including `bun test` error.
*   **20:05:13Z - 20:05:13Z:** Initial fix for `bun test` (renaming test files, updating playwright config, package.json scripts). Playwright test discovery confirmed.
*   **20:05:13Z - 20:05:13Z:** User criticizes for not running tests. Running `npm run test` reveals relay server errors (`Cannot perform I/O on behalf of a different request`).
*   **20:05:13Z - 20:05:13Z:** User corrects to use `bun` commands. `bunx playwright test` fails ("No tests found").
*   **20:05:13Z - 20:05:13Z:** Debugging `bunfig.toml` syntax and `bun test` behavior.
*   **20:05:13Z - 20:05:13Z:** Decision to replace Cloudflare Workers relay with a Node.js test relay due to persistent I/O errors. Implementation of `test-relay.cjs`.
*   **20:05:13Z - 20:05:13Z:** Fixing Node.js `require` vs. ES module syntax in `test-relay.cjs`.
*   **20:05:13Z - 20:05:13Z:** All Playwright tests pass with the new Node.js relay.
*   **20:05:13Z - 20:05:13Z:** User points out misleading "Known issue" in a test. Test is refactored to properly assert behavior. All tests pass cleanly.
*   **20:05:13Z - 20:05:13Z:** Task 1-7 marked as "Done."
*   **20:05:13Z - 20:05:13Z:** Start of Task 1-8 (User Identity System): Task document created, schema updated (`User` table, `authorDisplayName` in `Message`), `useUser` hook, `avatars.ts`, `ProfileSetupModal`, `UserAvatar` components created.
*   **20:05:13Z - 20:05:13Z:** Initial Playwright tests for user identity fail (modal not visible). Typecheck reveals many new/reintroduced TypeScript errors due to incorrect Evolu API usage in new hooks.
*   **20:05:13Z - 20:05:13Z:** Beginning of another major debugging cycle for Evolu API in user identity features.