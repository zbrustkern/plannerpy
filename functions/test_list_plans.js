const { initializeApp } = require('firebase-admin/app');
const { getFirestore } = require('firebase-admin/firestore');

const app = initializeApp({ projectId: 'planner-cac2a' });
const db = getFirestore();

async function test() {
  const users = await db.collection('users').limit(1).get();
  if (users.empty) {
    console.log("No users found");
    return;
  }
  const uid = users.docs[0].id;
  const plans = await db.collection(`users/${uid}/plans`).get();
  for (const plan of plans.docs) {
    const details = await plan.ref.collection('details').doc('main').get();
    console.log(plan.id, "details exists:", details.exists, "details data:", details.data());
  }
}
test().catch(console.error);
