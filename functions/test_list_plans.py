import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
  'projectId': 'planner-cac2a',
})

db = firestore.client()
users = db.collection('users').limit(1).get()
if not users:
    print("No users")
    exit()
uid = users[0].id
plans = db.collection(f'users/{uid}/plans').get()
for plan in plans:
    details_doc = db.collection(f'users/{uid}/plans/{plan.id}/details').document('main').get()
    print(plan.id, "details exists:", details_doc.exists, "data:", details_doc.to_dict())
