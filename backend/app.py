from flask import Flask, request, jsonify
from flask_cors import CORS
from agent import agent, AgentState
from config import config
import base64
import io
from PIL import Image
import uuid

app = Flask(__name__)
if config.CORS_ENABLED:
    CORS(app)

session_store = {}

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json or {}
        message = data.get('message', '').strip()
        context = data.get('context', '')
        image_data = data.get('image')
        session_id = data.get('sessionId') or data.get('session_id') or str(uuid.uuid4())
        sanitized_image = None
        image_metadata = None
        
        if image_data:
            try:
                payload = image_data.split(config.API_BASE64_DELIMITER)[1] if config.API_BASE64_DELIMITER in image_data else image_data
                image_bytes = base64.b64decode(payload)
                with Image.open(io.BytesIO(image_bytes)) as img:
                    image_metadata = {'width': img.size[0], 'height': img.size[1]}
                sanitized_image = payload
            except Exception as exc:
                print(f"Image processing error: {exc}")
                sanitized_image = None
        
        state = session_store.get(session_id)
        if not state:
            state = {
                "messages": [],
                "context": context,
                "pending_action": None,
                "action_params": None,
                "needs_confirmation": False,
                "image_data": None,
                "confirmation_message": None,
                "awaiting_confirmation": False,
                "confirmation_override": False
            }
        
        history = list(state.get('messages', []))
        if message:
            history.append({"role": "user", "content": message})
        
        state['messages'] = history
        state['context'] = context
        state['image_data'] = sanitized_image
        state.setdefault('awaiting_confirmation', False)
        state.setdefault('confirmation_override', False)
        state.setdefault('needs_confirmation', False)
        state.setdefault('confirmation_message', None)
        state.setdefault('pending_action', None)
        state.setdefault('action_params', None)
        
        result = agent.invoke(state, config={"recursion_limit": 5, "thread_id": session_id})
        session_store[session_id] = result
        
        response_text = None
        for msg in reversed(result.get('messages', [])):
            if isinstance(msg, dict) and msg.get('role') == 'assistant':
                response_text = msg.get('content')
                break
        
        if not response_text:
            response_text = config.DEFAULT_RESPONSE
        
        return jsonify({
            'response': response_text,
            'context': context,
            'image_processed': sanitized_image is not None,
            'sessionId': session_id,
            'awaitingConfirmation': result.get('awaiting_confirmation', False),
            'imageMetadata': image_metadata
        })
    except Exception as e:
        print(f"Chat error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'response': f"Sorry, I encountered an error: {str(e)}",
            'error': True
        }), 500

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    return jsonify({'text': config.SPEECH_TO_TEXT_ERROR, 'error': True}), 501

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    return jsonify({'status': config.TEXT_TO_SPEECH_ERROR, 'error': True}), 501

# Add API endpoints for data access
@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    try:
        from tools import get_all_vehicles
        vehicles = get_all_vehicles()
        payload = [dict(row) for row in vehicles]
        return jsonify({'vehicles': payload})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/drivers', methods=['GET'])
def get_drivers():
    try:
        from tools import get_all_drivers
        drivers = get_all_drivers()
        payload = [dict(row) for row in drivers]
        return jsonify({'drivers': payload})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trips', methods=['GET'])
def get_trips():
    try:
        from tools import get_trips_with_routes
        trips = get_trips_with_routes()
        return jsonify({'trips': trips})
    except Exception as e:
        import traceback
        print(f"Error in get_trips: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stops', methods=['GET'])
def get_stops():
    try:
        from tools import get_all_stops
        stops = get_all_stops()
        payload = [
            {
                'id': row['id'],
                'name': row['name'],
                'latitude': row['latitude'],
                'longitude': row['longitude']
            }
            for row in stops
        ]
        return jsonify({'stops': payload})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/paths', methods=['GET'])
def get_paths():
    try:
        from tools import get_paths_with_stops
        paths = get_paths_with_stops()
        return jsonify({'paths': paths})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/routes', methods=['GET'])
def get_routes():
    try:
        from tools import get_routes_with_paths
        routes = get_routes_with_paths()
        return jsonify({'routes': routes})
    except Exception as e:
        import traceback
        print(f"Error in get_routes: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/deployments', methods=['GET'])
def get_deployments():
    try:
        from tools import get_deployments_detailed
        deployments = get_deployments_detailed()
        return jsonify({'deployments': deployments})
    except Exception as e:
        import traceback
        print(f"Error in get_deployments: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': config.HEALTH_STATUS, 'mode': config.MODE})

if __name__ == '__main__':
    from tools import init_database
    print("Initializing database (migrations will run automatically)...")
    init_database()
    
    for msg in config.STARTUP_MESSAGES:
        print(msg)
    
    app.run(debug=config.FLASK_DEBUG, host=config.FLASK_HOST, port=config.FLASK_PORT)