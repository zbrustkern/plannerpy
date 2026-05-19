# PlannerPy

PlannerPy is the serverless Python backend powering **Tophat Financial**. It utilizes Firebase Cloud Functions (Python Gen 2) and Firestore to manage secure, user-specific financial planning data.

## 🚀 Features

- **Serverless Architecture**: Deployed on Google Cloud via Firebase Functions.
- **Secure by Default**: All endpoints strictly enforce Firebase Authentication and operate within isolated user context boundaries (`users/{uid}/plans`).
- **Flexible Data Modeling**: Supports dynamic plan types (Income, Savings, College, Tactical Allocation) by separating standard metadata from plan-specific subcollections (`details`).
- **CORS Configured**: Ready to securely accept cross-origin requests from the Tophat frontend.

## 📡 API Endpoints (Callable Functions)

All endpoints are exposed as Firebase Callable Functions (`@https_fn.on_call()`), meaning they automatically handle CORS, decode auth tokens, and cleanly pass JSON payloads.

| Function | Description | Payload |
| :--- | :--- | :--- |
| `create_plan` | Creates a new plan and writes specific data to the `details` subcollection. | `planName`, `planType`, `formData`, `details` (optional) |
| `read_plan` | Fetches a single plan by ID, including its `details` subcollection. | `planId` |
| `update_plan` | Updates standard metadata and recursively merges the `details` subcollection. | `planId`, `planName`, `details` (optional) |
| `delete_plan` | Deletes a plan and orchestrates the cleanup of its subcollections. | `planId` |
| `list_plans` | Streams all top-level plans belonging to the authenticated user. | None |

## 🏗️ Local Development

### Prerequisites
- Python 3.12+
- Firebase CLI (`npm install -g firebase-tools`)
- A Firebase Project with Cloud Functions and Firestore enabled.

### Setup
1. Clone this repository.
2. Navigate to the functions directory:
   ```bash
   cd functions
   ```
3. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running Locally
To test the functions locally with the Firebase Emulator Suite:
```bash
firebase emulators:start --only functions,firestore
```

## 🚀 Deployment

Make sure you are logged into the Firebase CLI (`firebase login`), and then run:

```bash
firebase deploy --only functions
```

## 🗄️ Database Structure

PlannerPy organizes data in Firestore using the following hierarchy to ensure fast queries and strict security boundaries:

```text
users/
└── {uid}/
    └── plans/
        └── {planId}/
            ├── planName: string
            ├── planType: string
            ├── createdAt: timestamp
            ├── lastUpdated: timestamp
            └── details/ (Subcollection)
                └── main/
                    └── ... (dynamic JSON depending on planType)
```
