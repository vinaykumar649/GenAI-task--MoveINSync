from tools import *
from typing import TypedDict, List, Optional, Dict, Any
import re
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    context: str
    pending_action: Optional[str]
    action_params: Optional[dict]
    needs_confirmation: bool
    image_data: Optional[str]
    confirmation_message: Optional[str]
    awaiting_confirmation: bool
    confirmation_override: bool

def extract_quoted_string(text: str, after_keywords: List[str] = None) -> Optional[str]:
    patterns = [
        r"['\"]([^'\"]+)['\"]",
        r"\[([^\]]+)\]"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    if after_keywords:
        for keyword in after_keywords:
            pattern = rf"{keyword}\s+['\"]?(\w[\w\s\-\.]*?)['\"]?(?:\s+(?:from|to|at|in|for|with|and|or)|$)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and len(value) > 1:
                    return value
    
    words = text.split()
    for i, word in enumerate(words):
        if word.lower() in [k.lower() for k in (after_keywords or [])]:
            if i + 1 < len(words):
                potential_value = ' '.join(words[i+1:i+4]).strip()
                if potential_value and len(potential_value) > 1:
                    return potential_value.rstrip('.,;')
    return None

def extract_license_plate(text: str) -> Optional[str]:
    patterns = [
        r"['\"]([A-Z]{2}-\d{2}-[A-Z]{0,2}-?\d{4})['\"]",
        r"([A-Z]{2}-\d{2}-[A-Z]{0,2}-?\d{4})",
        r"vehicle\s+['\"]?([^'\"]+?)['\"]?(?:\s+(?:and|or|to|with|driver)|$)",
        r"['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            plate = match.group(1).strip().upper()
            if plate and len(plate) > 3:
                return plate
    
    all_vehicles = get_all_vehicles()
    for vehicle in all_vehicles:
        try:
            plate = vehicle['license_plate']
            if plate and plate.upper() in text.upper():
                return plate.upper()
        except (KeyError, TypeError):
            pass
    
    return None

def extract_driver_name(text: str) -> Optional[str]:
    patterns = [
        r"driver\s+['\"]?([^'\"]+?)['\"]?(?:\s+(?:to|from|for|with|and)|$)",
        r"['\"]([^'\"]+)['\"]",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if name and len(name) > 1:
                return name
    
    extracted = extract_quoted_string(text, ["named", "driver"])
    if extracted:
        return extracted
    
    all_drivers = get_all_drivers()
    for driver in all_drivers:
        try:
            driver_name = driver['name']
            if driver_name.lower() in text.lower() or text.lower() in driver_name.lower():
                return driver_name
        except (KeyError, TypeError):
            pass
    
    return None

def extract_trip_identifier(text: str) -> Optional[str]:
    patterns = [
        r"trip\s+['\"]?([^'\"\s]+(?:\s+[^'\"\s]+)*)['\"]?",
        r"['\"]([^'\"]+)['\"]",
        r"from\s+['\"]?([^'\"]+?)['\"]?(?:\s+(?:trip|route)|$)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    all_trips = get_all_trips()
    for trip in all_trips:
        try:
            display_name = trip['display_name']
            if display_name.lower() in text.lower():
                return display_name
        except (KeyError, TypeError):
            pass
    
    return None

def extract_path_name(text: str) -> Optional[str]:
    patterns = [
        r"['\"]([^'\"]+)['\"]",
        r"path\s+['\"]?([^'\"\s]+(?:\s+[^'\"\s]+)*)['\"]?(?:\s+(?:to|has|contains|with)|$)",
        r"(?:for|using|on|in)\s+(?:the\s+)?path\s+['\"]?([^'\"]+?)['\"]?(?:\s+|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result = match.group(1).strip()
            if result:
                return result
    
    all_paths = get_all_paths()
    for path in all_paths:
        try:
            path_name = path['name']
            if path_name.lower() in text.lower():
                return path_name
        except (KeyError, TypeError):
            pass
    
    return None

def extract_stops_list(text: str) -> Optional[List[str]]:
    match = re.search(r"(?:using|with)\s+(?:stops?|the following)(?:\s+[:=])?\s*['\"]?([^'\"]+)['\"]?", text, re.IGNORECASE)
    if match:
        stops_str = match.group(1)
        return [s.strip() for s in re.split(r'[,;]|,\s+and\s+', stops_str) if s.strip()]
    
    match = re.search(r"\[([^\]]+)\]", text)
    if match:
        stops_str = match.group(1)
        return [s.strip() for s in re.split(r'[,;]', stops_str) if s.strip()]
    
    return None

def extract_route_name(text: str) -> Optional[str]:
    patterns = [
        r"route\s+['\"]?([^'\"]+?(?:\s+-\s+\d{1,2}:\d{2})?)['\"]?(?:\s+|$)",
        r"['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            route_name = match.group(1).strip()
            if route_name:
                return route_name
    
    all_routes = get_all_routes()
    for route in all_routes:
        try:
            route_display_name = route['route_display_name']
            if route_display_name.lower() in text.lower():
                return route_display_name
        except (KeyError, TypeError):
            pass
    
    return None

def get_first_path_id() -> int:
    paths = get_all_paths()
    return paths[0]['id'] if paths else 1

def get_sample_vehicle_config() -> Dict[str, Any]:
    vehicles = get_all_vehicles()
    if vehicles:
        try:
            capacity = int(vehicles[0]['capacity']) if 'capacity' in vehicles[0] else 50
        except (KeyError, TypeError, ValueError):
            capacity = 50
        try:
            model = vehicles[0]['model']
        except (KeyError, TypeError):
            model = 'Standard Bus'
        return {
            'capacity': capacity,
            'model': model
        }
    return {'capacity': 50, 'model': 'Standard Bus'}

def detect_action_intent(text: str) -> tuple:
    action = None
    params = {}
    
    text_lower = text.lower()
    
    action_verbs = r'\b(show|list|display|get|check|find|remove|delete|unassign|assign|allocate|add|create|update)\b'
    action_match = re.search(action_verbs, text_lower)
    action_verb = action_match.group(1) if action_match else 'show'
    
    entity_patterns = [
        (r'vehicle[s]?', 'vehicles'),
        (r'driver[s]?', 'drivers'),
        (r'trip[s]?', 'trips'),
        (r'route[s]?', 'routes'),
        (r'path[s]?', 'paths'),
        (r'stop[s]?', 'stops'),
        (r'deployment[s]?|assignment[s]?', 'deployments'),
    ]
    
    detected_entity = None
    for pattern, entity_type in entity_patterns:
        if re.search(pattern, text_lower):
            detected_entity = entity_type
            break
    
    if action_verb in ['remove', 'delete', 'unassign']:
        if 'vehicle' in text_lower:
            trip_name = extract_trip_identifier(text)
            if trip_name:
                return ('remove_vehicle_from_trip_by_name', {'trip_name': trip_name})
    
    if action_verb in ['assign', 'allocate']:
        if ('vehicle' in text_lower or 'driver' in text_lower) and 'trip' in text_lower:
            vehicle = extract_license_plate(text)
            driver = extract_driver_name(text)
            trip = extract_trip_identifier(text)
            if vehicle or driver or trip:
                return ('assign_vehicle_driver', {'vehicle': vehicle, 'driver': driver, 'trip': trip})
    
    if action_verb in ['create', 'add']:
        if 'stop' in text_lower:
            stop_name = extract_quoted_string(text, ["called", "named", "stop"])
            return ('create_stop', {"name": stop_name or "New Stop", "lat": 0.0, "lng": 0.0})
        elif 'path' in text_lower:
            path_name = extract_quoted_string(text, ["called", "named", "path"])
            return ('create_path', {"name": path_name or "New Path"})
        elif 'vehicle' in text_lower:
            license_plate = extract_license_plate(text)
            vehicle_config = get_sample_vehicle_config()
            return ('create_vehicle', {"license_plate": license_plate or "XX-XX-XXXX", "capacity": vehicle_config['capacity'], "model": vehicle_config['model']})
        elif 'driver' in text_lower:
            driver_name = extract_driver_name(text)
            return ('create_driver', {"name": driver_name or "New Driver", "license": "DL0000000", "phone": "9000000000"})
    
    if 'unassigned' in text_lower or 'available' in text_lower or 'free' in text_lower:
        if 'vehicle' in text_lower:
            return ('get_unassigned_vehicles', {})
        elif 'driver' in text_lower:
            return ('get_unassigned_drivers', {})
    
    if action_verb in ['list', 'show', 'display', 'get']:
        if detected_entity == 'vehicles':
            return ('list_all_vehicles', {})
        elif detected_entity == 'drivers':
            return ('list_all_drivers', {})
        elif detected_entity == 'trips':
            return ('list_all_trips', {})
        elif detected_entity == 'stops':
            return ('list_all_stops', {})
        elif detected_entity == 'routes':
            if 'path' in text_lower:
                path_name = extract_path_name(text)
                if path_name:
                    return ('list_routes_using_path', {'path_name': path_name})
            return ('list_all_routes', {})
        elif detected_entity == 'paths':
            return ('list_all_paths', {})
        elif detected_entity == 'deployments':
            return ('list_all_deployments', {})
        
        if 'stop' in text_lower and ('route' in text_lower or 'path' in text_lower):
            if 'route' in text_lower:
                route_name = extract_route_name(text)
                if route_name:
                    return ('list_stops_for_route', {'route_name': route_name})
            if 'path' in text_lower:
                path_name = extract_path_name(text)
                if path_name:
                    return ('list_stops_for_path', {'path_name': path_name})
        
        if 'status' in text_lower and 'trip' in text_lower:
            trip_name = extract_quoted_string(text)
            if trip_name:
                return ('get_trip_status_by_name', {'trip_name': trip_name})
    
    return (None, {})

def start_node(state: AgentState) -> AgentState:
    messages = state['messages']
    if not messages or not isinstance(messages[-1], dict):
        return state
    
    last_message = messages[-1]
    if last_message.get('role') != 'user':
        return state
    
    text = last_message.get('content', '').lower()
    
    if state.get('awaiting_confirmation'):
        if re.search(r'\b(yes|yep|yeah|sure|confirm|proceed|okay|ok|go ahead)\b', text):
            state['awaiting_confirmation'] = False
            state['confirmation_override'] = True
            state['needs_confirmation'] = False
            return state
        if re.search(r'\b(no|nope|cancel|stop|abort|nevermind|never mind)\b', text) or "don't" in text or "do not" in text:
            state['awaiting_confirmation'] = False
            state['confirmation_override'] = False
            state['pending_action'] = None
            state['action_params'] = None
            state['needs_confirmation'] = False
            state['confirmation_message'] = None
            state['messages'] = messages + [{"role": "assistant", "content": "Understood. I have cancelled that request."}]
            return state
        state['messages'] = messages + [{"role": "assistant", "content": "Please confirm with yes or no, or say cancel to stop the previous action."}]
        return state
    
    pending_action, action_params = detect_action_intent(last_message.get('content', ''))
    
    state['needs_confirmation'] = False
    state['confirmation_message'] = None
    state['confirmation_override'] = False
    
    if pending_action:
        state['pending_action'] = pending_action
        state['action_params'] = action_params or {}
        return state
    
    state['pending_action'] = None
    state['action_params'] = None
    state['messages'] = messages + [{"role": "assistant", "content": "I can help with: listing vehicles/drivers/routes/paths/stops/trips, showing stops for a route/path, checking trip status, assigning vehicles/drivers, removing assignments, or creating new items. What would you like to do?"}]
    return state

def check_consequences(state: AgentState) -> AgentState:
    pending_action = state.get('pending_action')
    if not pending_action:
        state['needs_confirmation'] = False
        state['confirmation_message'] = None
        return state
    
    if state.get('awaiting_confirmation') or state.get('confirmation_override'):
        return state
    
    action_params = state.get('action_params') or {}
    needs_confirmation = False
    confirmation_message = None
    
    if pending_action == "remove_vehicle_from_trip_by_name":
        trip_name = action_params.get('trip_name')
        if trip_name:
            trip_id = find_trip_by_display_name(trip_name)
            if trip_id:
                booked = check_trip_booked_percentage(trip_id)
                if booked > 0.0:
                    needs_confirmation = True
                    confirmation_message = f"Trip '{trip_name}' is {booked*100:.0f}% booked. Removing vehicle will cancel bookings. Proceed?"
    
    state['needs_confirmation'] = needs_confirmation
    state['confirmation_message'] = confirmation_message
    return state

def get_confirmation(state: AgentState) -> AgentState:
    messages = state['messages']
    confirmation_msg = state.get('confirmation_message') or 'This action requires confirmation.'
    prompt = f"{confirmation_msg} Please respond with yes or no."
    state['messages'] = messages + [{"role": "assistant", "content": prompt}]
    state['needs_confirmation'] = False
    state['awaiting_confirmation'] = True
    return state

def execute_action(state: AgentState) -> AgentState:
    action = state.get('pending_action')
    params = state.get('action_params') or {}
    messages = state['messages']
    context = state.get('context', '')
    
    if not action:
        state['pending_action'] = None
        state['action_params'] = None
        return state
    
    response = ""
    
    try:
        if action == "get_unassigned_vehicles":
            result = get_unassigned_vehicles()
            count = len(result)
            plates = [row["license_plate"] for row in result]
            response = f"Found {count} unassigned vehicles: {', '.join(plates)}" if plates else f"Found {count} unassigned vehicles"
        
        elif action == "get_unassigned_drivers":
            result = get_unassigned_drivers()
            count = len(result)
            names = [row["name"] for row in result]
            response = f"Found {count} unassigned drivers: {', '.join(names)}" if names else f"Found {count} unassigned drivers"
        
        elif action == "create_stop":
            stop_id = create_stop(params['name'], params['lat'], params['lng'])
            response = f"Created stop '{params['name']}' with ID {stop_id}"
        
        elif action == "create_path":
            path_id = create_path(params['name'])
            response = f"Created path '{params['name']}' with ID {path_id}"
        
        elif action == "create_vehicle":
            vehicle_id = create_vehicle(params['license_plate'], 'Bus', params['capacity'], params['model'])
            response = f"Created vehicle '{params['license_plate']}' with ID {vehicle_id}"
        
        elif action == "create_driver":
            driver_id = create_driver(params['name'], params['license'], params['phone'])
            response = f"Created driver '{params['name']}' with ID {driver_id}"
        
        elif action == "assign_vehicle_driver":
            vehicle_plate = params.get('vehicle')
            driver_name = params.get('driver')
            trip_name = params.get('trip')
            
            if not (vehicle_plate or driver_name or trip_name):
                response = "Please specify a vehicle, driver, and trip to assign."
            else:
                trip_id = find_trip_by_display_name(trip_name) if trip_name else None
                vehicle_id = find_vehicle_by_plate(vehicle_plate) if vehicle_plate else None
                driver_id = find_driver_by_name(driver_name) if driver_name else None
                
                if not trip_id:
                    response = f"Trip '{trip_name}' not found. Please check the trip name."
                elif not vehicle_id:
                    response = f"Vehicle '{vehicle_plate}' not found. Please check the vehicle plate."
                elif not driver_id:
                    response = f"Driver '{driver_name}' not found. Please check the driver name."
                else:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM deployments WHERE trip_id = ?', (trip_id,))
                        deployment_id = assign_vehicle_driver(trip_id, vehicle_id, driver_id)
                        conn.commit()
                        conn.close()
                        response = f"Assigned vehicle {vehicle_plate} and driver {driver_name} to trip '{trip_name}' (Deployment ID: {deployment_id})"
                    except Exception as e:
                        response = f"Error assigning vehicle and driver: {str(e)}"
        
        elif action == "list_all_vehicles":
            vehicles = get_all_vehicles()
            if vehicles:
                formatted = ", ".join([f"{row['license_plate']} ({row['model']})" for row in vehicles])
                response = f"All vehicles ({len(vehicles)}): {formatted}"
            else:
                response = "No vehicles found."
        
        elif action == "list_all_drivers":
            drivers = get_all_drivers()
            if drivers:
                formatted = ", ".join([f"{row['name']} ({row['license_number']})" for row in drivers])
                response = f"All drivers ({len(drivers)}): {formatted}"
            else:
                response = "No drivers found."
        
        elif action == "list_all_trips":
            trips = get_trips_with_routes()
            if trips:
                formatted = "; ".join([f"Trip {row['id']}: {row['route_name']} on {row['date']} ({row['live_status']}, {row['booking_status_percentage']*100:.0f}% booked)" for row in trips])
                response = f"All trips ({len(trips)}): {formatted}"
            else:
                response = "No trips scheduled."
        
        elif action == "list_all_stops":
            stops = get_all_stops()
            if stops:
                formatted = ", ".join([row['name'] for row in stops])
                response = f"All stops ({len(stops)}): {formatted}"
            else:
                response = "No stops defined."
        
        elif action == "list_all_routes":
            routes = get_routes_with_paths()
            if routes:
                formatted = "; ".join([f"{row['route_display_name']} ({row['path_name']}, {row['shift_time']})" for row in routes])
                response = f"All routes ({len(routes)}): {formatted}"
            else:
                response = "No routes found."
        
        elif action == "list_all_paths":
            paths = get_paths_with_stops()
            if paths:
                formatted_paths = []
                for path in paths:
                    stop_names = " → ".join([stop['name'] for stop in path['stops']]) if path['stops'] else "No stops"
                    formatted_paths.append(f"{path['name']} ({stop_names})")
                response = f"All paths ({len(paths)}): {'; '.join(formatted_paths)}"
            else:
                response = "No paths available."
        
        elif action == "list_all_deployments":
            deployments = get_deployments_detailed()
            if deployments:
                formatted = []
                for item in deployments:
                    formatted.append(f"{item['trip_display_name']} → {item['license_plate']} ({item['driver_name']})")
                response = f"Active deployments ({len(deployments)}): {'; '.join(formatted)}"
            else:
                response = "No active deployments."
        
        elif action == "list_stops_for_route":
            route_name = params.get('route_name')
            if not route_name:
                response = "Please specify a route name."
            else:
                routes = get_routes_with_paths()
                matching_route = None
                
                for route in routes:
                    try:
                        display_name = route['route_display_name']
                    except (KeyError, TypeError):
                        display_name = ''
                    if route_name and display_name and (route_name.lower() in display_name.lower() or display_name.lower() in route_name.lower()):
                        matching_route = route
                        break
                
                if matching_route:
                    try:
                        path_name = matching_route['path_name']
                    except (KeyError, TypeError):
                        path_name = None
                    stops = get_stops_for_path(path_name) if path_name else []
                    if stops:
                        response = f"Stops on route '{route_name}': {' → '.join(stops)}"
                    else:
                        response = f"No stops found on route '{route_name}'."
                else:
                    response = f"Route '{route_name}' not found."
        
        elif action == "list_stops_for_path":
            path_name = params.get('path_name')
            if not path_name:
                response = "Please specify a path name."
            else:
                stops = get_stops_for_path(path_name)
                if stops:
                    response = f"Stops for '{path_name}': {' → '.join(stops)}"
                else:
                    response = f"No stops found for path '{path_name}'."
        
        elif action == "list_routes_using_path":
            path_name = params.get('path_name')
            if not path_name:
                response = "Please specify a path name."
            else:
                routes = get_routes_using_path(path_name)
                if routes:
                    formatted = ", ".join([f"{r['route_display_name']} ({r['shift_time']})" for r in routes])
                    response = f"Routes using '{path_name}': {formatted}"
                else:
                    response = f"No routes found using path '{path_name}'."
        
        elif action == "get_trip_status_by_name":
            trip_name = params.get('trip_name')
            if not trip_name:
                response = "Please specify a trip name."
            else:
                trip_info = get_trip_status_by_name(trip_name)
                if trip_info:
                    response = f"Trip '{trip_info['display_name']}': {trip_info['booking_status_percentage']*100:.0f}% booked, Status: {trip_info['live_status']}, Date: {trip_info['date']}"
                    try:
                        if trip_info['license_plate']:
                            driver_name = trip_info.get('driver_name', 'Not assigned')
                            response += f", Vehicle: {trip_info['license_plate']}, Driver: {driver_name}"
                    except (KeyError, TypeError):
                        pass
                else:
                    response = f"Trip '{trip_name}' not found."
        
        elif action == "remove_vehicle_from_trip_by_name":
            trip_name = params.get('trip_name')
            if not trip_name:
                response = "Please specify a trip name."
            else:
                trip_id = find_trip_by_display_name(trip_name)
                if trip_id:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM deployments WHERE trip_id = ?', (trip_id,))
                    removed = cursor.rowcount
                    conn.commit()
                    conn.close()
                    response = f"Removed vehicle assignment from trip '{trip_name}'" if removed else f"No vehicle assignment found for trip '{trip_name}'"
                else:
                    response = f"Trip '{trip_name}' not found."
        
        else:
            response = f"Action '{action}' not implemented yet."
    
    except Exception as e:
        response = f"Error executing {action}: {str(e)}"
    
    state['messages'] = messages + [{"role": "assistant", "content": response}]
    state['pending_action'] = None
    state['action_params'] = None
    state['needs_confirmation'] = False
    state['confirmation_message'] = None
    state['awaiting_confirmation'] = False
    state['confirmation_override'] = False
    state['image_data'] = None
    
    return state

def route_to_action(state: AgentState) -> str:
    if state.get('needs_confirmation'):
        return "get_confirmation"
    elif state.get('pending_action'):
        return "execute_action"
    else:
        return END

def build_agent():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("start", start_node)
    workflow.add_node("check_consequences", check_consequences)
    workflow.add_node("get_confirmation", get_confirmation)
    workflow.add_node("execute_action", execute_action)
    
    workflow.add_edge("start", "check_consequences")
    workflow.add_conditional_edges("check_consequences", route_to_action)
    workflow.add_edge("get_confirmation", END)
    workflow.add_edge("execute_action", END)
    
    workflow.set_entry_point("start")
    
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

agent = build_agent()
