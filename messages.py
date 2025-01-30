from flask import jsonify, request, make_response
from flask_restful import Resource

from data import connect

def get_conversation_id(sender_id, receiver_id, db):
    conversation_query = f'''SELECT *
                        FROM mmu.conversations
                        WHERE conversation_user_id_1 = LEAST("{sender_id}","{receiver_id}") AND conversation_user_id_2 = GREATEST("{sender_id}","{receiver_id}");'''
    print('executing conversation query 1')
    response = db.execute(conversation_query)

    return response

class Messages(Resource):

    def get(self):
        print("In Messages GET")

        sender_id = request.args.get('sender_id')
        receiver_id = request.args.get('receiver_id')

        with connect() as db:

            try:
                response = get_conversation_id(sender_id, receiver_id, db)
                
                if not response['result']:
                    return jsonify({
                        "message": "No conversation between these users"
                    })
                else:
                    conversation_id = response['result'][0]['conversation_uid']
                
                message_query = f'''SELECT *
                                    FROM mmu.messages
                                    WHERE message_conversation_id = "{conversation_id}";'''
                
                response = db.execute(message_query)

                return response
            
            except:
                return make_response(jsonify({
                    "message": "Error in GET method"
                }), 400)


    def post(self):
        print("In Messages POST")
        
        data = request.get_json()
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        message_content = data['message_content']

        with connect() as db:

            try:
                # checking if conversation id exists between 2 users or not

                response = get_conversation_id(sender_id, receiver_id, db)

                if not response['result']:
                    new_conversation_id = db.call(procedure='new_conversation_uid')
                    new_conversation_id = new_conversation_id['result'][0]['new_id']
                    data['conversation_uid'] = new_conversation_id

                    conversation_query = f'''INSERT INTO mmu.conversations (conversation_uid, conversation_user_id_1, conversation_user_id_2)
                                        VALUES ("{new_conversation_id}",LEAST("{sender_id}","{receiver_id}"),GREATEST("{sender_id}","{receiver_id}"));'''
                    response = db.execute(conversation_query, cmd='post')

                else: 
                    new_conversation_id = response['result'][0]['conversation_uid']
                
                # adding messages
                new_message_id = db.call(procedure='new_message_uid')
                new_message_id = new_message_id['result'][0]['new_id']
                message_query = f'''INSERT INTO mmu.messages (message_uid, message_conversation_id, message_sender_user_id, message_content)
                                VALUES ("{new_message_id}","{new_conversation_id}","{sender_id}","{message_content}")'''
                
                
                response = db.execute(message_query, cmd="post")
                response['message_uid'] = new_message_id
                
                return response

            except:
                return make_response(jsonify({
                    "message": "Error in POST method"
                }), 400)