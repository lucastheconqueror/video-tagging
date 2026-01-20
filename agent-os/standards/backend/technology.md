# Backend & Server Architecture (Firebase + Next.js)

## Core Stack
- **Runtime:** Node.js (Standard Runtime required for `firebase-admin`)
- **Database:** Firestore (NoSQL)
- **Auth:** Firebase Auth (Client SDK) + `firebase-admin` (Server Verification)
- **Storage:** Google Cloud Storage (via Signed URLs)
- **Validation:** Zod (Strict input validation)

## Architecture & Data Flow
**Follow this "Hybrid" approach strictly:**

1.  **Server Actions (`src/app/_actions` or `src/server/actions`)**
    - **Usage:** Primary method for mutations (writes/updates) and sensitive logic.
    - **Privilege:** Use `firebase-admin` (initialized globally) to bypass client-side rules.
    - **Security:**
        - **Auth Check:** MUST verify the user's session token *inside* the action before processing.
        - **Validation:** Validate all inputs with Zod before touching Firestore.
    - **Return:** Standardized object: `{ success: boolean, data?: any, error?: string }`.

2.  **Data Fetching (Server Components)**
    - **Usage:** Fetch data directly in Server Components using `firebase-admin`.
    - **Pattern:** `const snapshot = await adminDb.collection('...').get()`.
    - **Serialization:** Convert Firestore Timestamps to plain Dates/strings *before* passing to Client Components to avoid serialization errors.

3.  **Client-Side Operations**
    - **Realtime:** Use `firebase/firestore` (Client SDK) *only* when realtime listeners are strictly necessary (e.g., live chat).
    - **Auth:** Handle login/signup on the client (`signInWith...`), then sync session via a Server Action or Middleware if needed.

## File Storage Strategy (Google Cloud Storage)
**Do not upload files directly to the Next.js server.**

1.  **Pattern:** Signed URLs (Direct-to-Bucket Upload)
    - **Step 1 (Server Action):** Client requests a upload URL. Server Action validates permission and generates a V4 Signed URL using `@google-cloud/storage`.
    - **Step 2 (Client):** Frontend `PUT`s the file directly to the generated URL.
    - **Step 3 (Server Action):** (Optional) Client triggers a "confirmation" action to update Firestore with the new file URL.

## Security & Best Practices
- **Environment:**
    - `FIREBASE_SERVICE_ACCOUNT_KEY`: Store as a single minified JSON string or mapped individual vars in `.env.local`.
    - **Never** expose Admin keys to the client (`NEXT_PUBLIC_` prefix forbidden for admin creds).
- **Edge Runtime:** **AVOID.** Use the standard Node.js runtime. `firebase-admin` is not fully Edge-compatible.
- **Cold Starts:** Initialize the Admin app using a singleton pattern to prevent multiple instance errors during hot reloads.

## Code Standards
- **Collections:** Define collection names in a `src/lib/constants.ts` file (e.g., `COLLECTION.USERS`) to avoid magic strings.
- **Timestamps:** Use server-side timestamps (`FieldValue.serverTimestamp()`) for `createdAt`/`updatedAt`.

