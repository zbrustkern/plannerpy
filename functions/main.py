from firebase_functions import https_fn
from firebase_admin import initialize_app, firestore
import google.cloud.firestore
from firebase_functions.options import CorsOptions

app = initialize_app()

# Configure CORS
cors = CorsOptions(
    cors_origins=["*"],
    cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# Generic Plan CRUD operations
# Commenting to test push

@https_fn.on_call()
def create_plan(req: https_fn.CallableRequest) -> dict:
    if not req.auth:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
                                  message='User must be authenticated to create a plan.')

    uid = req.auth.uid
    data = req.data

    if not isinstance(data, dict) or 'planName' not in data or 'planType' not in data:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                                  message='Invalid request data.')

    plan_data = {
        'planName': data.get('planName', 'Untitled Plan'),
        'planType': data['planType'],
        'formData': data.get('formData', {}),
        'createdAt': firestore.SERVER_TIMESTAMP,
        'lastUpdated': firestore.SERVER_TIMESTAMP
    }

    firestore_client: google.cloud.firestore.Client = firestore.client()

    try:
        doc_ref = firestore_client.collection(f'users/{uid}/plans').document()
        doc_ref.set(plan_data)
        return {'success': True, 'message': 'Plan created successfully.', 'planId': doc_ref.id}
    except Exception as e:
        print(f"Error creating plan: {str(e)}")
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INTERNAL,
                                  message='Error creating plan.')


@https_fn.on_call()
def read_plan(req: https_fn.CallableRequest) -> dict:
    if not req.auth:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
                                  message='User must be authenticated to read a plan.')

    uid = req.auth.uid
    data = req.data

    if not isinstance(data, dict) or 'planId' not in data:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                                  message='Invalid request data.')

    plan_id = data['planId']
    firestore_client: google.cloud.firestore.Client = firestore.client()

    try:
        doc_ref = firestore_client.collection(f'users/{uid}/plans').document(plan_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.NOT_FOUND,
                                      message='Plan not found.')

        plan_data = doc.to_dict()
        
        # Get plan-specific details
        details_ref = doc_ref.collection('details').document('main')
        details_doc = details_ref.get()
        if details_doc.exists:
            plan_data['details'] = details_doc.to_dict()

        return {'success': True, 'plan': plan_data}
    except Exception as e:
        print(f"Error reading plan: {str(e)}")
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INTERNAL,
                                  message='Error reading plan.')

@https_fn.on_call()
def update_plan(req: https_fn.CallableRequest) -> dict:
    if not req.auth:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
                                  message='User must be authenticated to update a plan.')

    uid = req.auth.uid
    data = req.data

    if not isinstance(data, dict) or 'planId' not in data or 'planName' not in data:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                                  message='Invalid request data.')

    plan_id = data['planId']
    plan_data = {
        'planName': data['planName'],
        'lastUpdated': firestore.SERVER_TIMESTAMP
    }

    firestore_client: google.cloud.firestore.Client = firestore.client()

    try:
        doc_ref = firestore_client.collection(f'users/{uid}/plans').document(plan_id)
        doc_ref.update(plan_data)

        # Update plan-specific details
        if 'details' in data:
            details_ref = doc_ref.collection('details').document('main')
            details_ref.set(data['details'], merge=True)

        return {'success': True, 'message': 'Plan updated successfully.'}
    except Exception as e:
        print(f"Error updating plan: {str(e)}")
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INTERNAL,
                                  message='Error updating plan.')

@https_fn.on_call()
def delete_plan(req: https_fn.CallableRequest) -> dict:
    if not req.auth:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
                                  message='User must be authenticated to delete a plan.')

    uid = req.auth.uid
    data = req.data

    if not isinstance(data, dict) or 'planId' not in data:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                                  message='Invalid request data.')

    plan_id = data['planId']
    firestore_client: google.cloud.firestore.Client = firestore.client()

    try:
        doc_ref = firestore_client.collection(f'users/{uid}/plans').document(plan_id)
        # Delete plan-specific details subcollection
        details_ref = doc_ref.collection('details').document('main')
        details_ref.delete()
        # Delete main plan document
        doc_ref.delete()

        return {'success': True, 'message': 'Plan deleted successfully.'}
    except Exception as e:
        print(f"Error deleting plan: {str(e)}")
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INTERNAL,
                                  message='Error deleting plan.')

@https_fn.on_call()
def list_plans(req: https_fn.CallableRequest) -> dict:
    if not req.auth:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
                                  message='User must be authenticated to list plans.')

    uid = req.auth.uid
    firestore_client: google.cloud.firestore.Client = firestore.client()

    try:
        plans = firestore_client.collection(f'users/{uid}/plans').stream()
        plans_list = []
        for plan in plans:
            plan_dict = plan.to_dict()
            last_updated = plan_dict.get('lastUpdated')
            # Convert Firestore timestamp to string timestamp if it exists
            if last_updated and hasattr(last_updated, 'isoformat'):
                last_updated = last_updated.isoformat()
            
            plans_list.append({
                'id': plan.id,
                'planName': plan_dict.get('planName'),
                'planType': plan_dict.get('planType'),
                'formData': plan_dict.get('formData', {}),
                'lastUpdated': last_updated
            })
        return {'success': True, 'plans': plans_list}
    except Exception as e:
        print(f"Error listing plans: {str(e)}")
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INTERNAL,
                                  message='Error listing plans.')