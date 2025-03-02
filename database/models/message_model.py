from sqlalchemy import text

class MessageModel:
    """Message data operations"""
    
    @staticmethod
    def send_message(conn, sender_type, sender_id, receiver_type, receiver_id, message_text):
        """Send a new message."""
        conn.execute(text('''
        INSERT INTO messages 
        (sender_type, sender_id, receiver_type, receiver_id, message_text, is_read)
        VALUES (:sender_type, :sender_id, :receiver_type, :receiver_id, :message_text, FALSE)
        '''), {
            'sender_type': sender_type,
            'sender_id': sender_id,
            'receiver_type': receiver_type,
            'receiver_id': receiver_id,
            'message_text': message_text
        })
        conn.commit()
    
    @staticmethod
    def mark_as_read(conn, message_id):
        """Mark a message as read."""
        conn.execute(text('UPDATE messages SET is_read = TRUE WHERE id = :id'), 
                    {'id': message_id})
        conn.commit()
    
    @staticmethod
    def get_messages_for_admin(conn):
        """Get all messages for admin."""
        result = conn.execute(text('''
        SELECT m.id, m.sender_type, m.sender_id, m.message_text, m.is_read, m.created_at,
               CASE WHEN m.sender_type = 'company' THEN c.company_name ELSE 'Admin' END as sender_name
        FROM messages m
        LEFT JOIN companies c ON m.sender_type = 'company' AND m.sender_id = c.id
        WHERE m.receiver_type = 'admin'
        ORDER BY m.created_at DESC
        '''))
        return result.fetchall()
    
    @staticmethod
    def get_messages_for_company(conn, company_id):
        """Get all messages for a specific company."""
        result = conn.execute(text('''
        SELECT m.id, m.sender_type, m.sender_id, m.message_text, m.is_read, m.created_at,
               CASE WHEN m.sender_type = 'admin' THEN 'Admin' ELSE c.company_name END as sender_name
        FROM messages m
        LEFT JOIN companies c ON m.sender_type = 'company' AND m.sender_id = c.id
        WHERE (m.receiver_type = 'company' AND m.receiver_id = :company_id)
           OR (m.sender_type = 'company' AND m.sender_id = :company_id)
        ORDER BY m.created_at DESC
        '''), {'company_id': company_id})
        return result.fetchall()