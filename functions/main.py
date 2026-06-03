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
        
        # Save plan-specific details to subcollection
        if 'details' in data:
            details_ref = doc_ref.collection('details').document('main')
            details_ref.set(data['details'])

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
            
            # Fetch details subcollection
            details_ref = firestore_client.collection(f'users/{uid}/plans/{plan.id}/details').document('main')
            details_doc = details_ref.get()
            details_data = details_doc.to_dict() if details_doc.exists else {}

            plans_list.append({
                'id': plan.id,
                'planName': plan_dict.get('planName'),
                'planType': plan_dict.get('planType'),
                'details': details_data,
                'lastUpdated': last_updated
            })
        return {'success': True, 'plans': plans_list}
    except Exception as e:
        print(f"Error listing plans: {str(e)}")
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INTERNAL,
                                  message='Error listing plans.')
import requests
import datetime
from firebase_functions import scheduler_fn

def fetch_yahoo_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get('chart', {}).get('result', [{}])[0].get('meta', {}).get('regularMarketPrice')
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
    return None

@https_fn.on_call()
def fetch_quote(req: https_fn.CallableRequest) -> dict:
    if not req.auth:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
                                  message='User must be authenticated.')
    data = req.data
    symbol = data.get('symbol')
    if not symbol:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                                  message='symbol is required.')
    
    price = fetch_yahoo_price(symbol)
    if price is None:
        return {'success': False, 'message': 'Failed to fetch price.'}
    
    return {'success': True, 'price': price}

def _take_snapshot_for_plan(uid, plan_id, plan_dict, details_data, firestore_client):
    try:
        if plan_dict.get('planType') == 'rebalance' and 'assets' in details_data:
            updated_assets = []
            for asset in details_data.get('assets', []):
                if asset.get('type') == 'equity' and asset.get('symbol'):
                    price = fetch_yahoo_price(asset['symbol'])
                    if price is not None:
                        asset['price'] = price
                updated_assets.append(asset)
            details_data['assets'] = updated_assets

        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        snapshot_ref = firestore_client.collection(f'users/{uid}/plans/{plan_id}/history').document(today_str)
        snapshot_ref.set({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'planType': plan_dict.get('planType'),
            'details': details_data
        })
        return True
    except Exception as e:
        print(f"Failed to snapshot plan {plan_id}: {e}")
        return False

@https_fn.on_call()
def take_snapshot(req: https_fn.CallableRequest) -> dict:
    if not req.auth:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
                                  message='User must be authenticated.')
    uid = req.auth.uid
    data = req.data
    plan_id = data.get('planId')
    if not plan_id:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                                  message='planId is required.')

    firestore_client = firestore.client()
    try:
        doc_ref = firestore_client.collection(f'users/{uid}/plans').document(plan_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {'success': False, 'message': 'Plan not found.'}
        
        details_doc = doc_ref.collection('details').document('main').get()
        details_data = details_doc.to_dict() if details_doc.exists else {}

        _take_snapshot_for_plan(uid, plan_id, doc.to_dict(), details_data, firestore_client)
        return {'success': True, 'message': 'Snapshot taken successfully.'}
    except Exception as e:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INTERNAL,
                                  message=str(e))

@scheduler_fn.on_schedule(schedule="0 0 1 * *")
def monthly_snapshot(event: scheduler_fn.ScheduledEvent) -> None:
    firestore_client = firestore.client()
    users_ref = firestore_client.collection('users')
    
    for user_doc in users_ref.stream():
        uid = user_doc.id
        plans = firestore_client.collection(f'users/{uid}/plans').stream()
        for plan in plans:
            try:
                details_doc = firestore_client.collection(f'users/{uid}/plans/{plan.id}/details').document('main').get()
                details_data = details_doc.to_dict() if details_doc.exists else {}
                _take_snapshot_for_plan(uid, plan.id, plan.to_dict(), details_data, firestore_client)
            except Exception as e:
                print(f"Error processing plan {plan.id} for user {uid}: {e}")
