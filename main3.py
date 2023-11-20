import os
import hashlib
import json
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
api = Api(app)

# Установка конфигурации БД
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Модель для хранения инцидентов в базе данных
class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    headers = db.Column(db.String)
    body = db.Column(db.String)
    hash_value = db.Column(db.String, unique=True)

    @staticmethod
    def generate_hash(headers, body):
        relevant_headers = {k: v for k, v in headers.items()
                            if k in ['Content-Type', 'User-Agent']}
        headers_sorted = json.dumps(relevant_headers, sort_keys=True)
        body_sorted = json.dumps(body, sort_keys=True)
        return hashlib.sha256((headers_sorted + body_sorted).encode(
            'utf-8')).hexdigest()


# Создание таблицы в БД
with app.app_context():
    db.create_all()


class Problems(Resource):
    def post(self):
        headers_dict = {k: v for k, v in request.headers.items()}
        body = request.get_json(force=True)
        hash_value = Incident.generate_hash(headers_dict, body)

        existing_incident = Incident.query.filter_by(
            hash_value=hash_value).first()
        if existing_incident is None:
            # Создание нового инцидента, если его хеш-значение не существует в базе данных
            incident = Incident(headers=json.dumps(headers_dict),
                                body=json.dumps(body),
                                hash_value=hash_value)
            db.session.add(incident)
            db.session.commit()
        else:
            # Возвращение хеш-значения инцидента, если он уже существует в базе данных
            return {"hash": existing_incident.hash_value}, 200

        # Возвращение успешного ответа с хеш-значением нового инцидента
        return {"hash": hash_value}, 201


class Find(Resource):
    def post(self):
        search_query = request.get_json(force=True)
        search_results = []

        for key, value in search_query.items():
            # Поиск инцидентов, содержащих заданные ключи и значения в заголовках и теле
            search_results.extend(
                [i for i in Incident.query.filter(
                     Incident.headers.contains(key)).filter(
                     Incident.headers.contains(value))
                 ]
                + [i for i in Incident.query.filter(
                    Incident.body.contains(key)).filter(
                    Incident.body.contains(value))]
            )

        # Оставляем только уникальные записи инцидентов
        unique_records = {incident.hash_value: incident
                          for incident in search_results}.values()

        # Преобразование результатов поиска в формат JSON
        return jsonify([{"headers": json.loads(incident.headers),
                         "body": json.loads(incident.body)}
                        for incident in unique_records])


class Find2(Resource):
    def get(self):
        hash_value = request.args.get('h')
        incident = (Incident.query.filter_by(hash_value=hash_value).
                    first())
        if incident:
            # Если найден инцидент с заданным хеш-значением, вернуть его
            return jsonify({"headers": json.loads(incident.headers),
                            "body": json.loads(incident.body)})
        else:
            # Если инцидент не найден, вернуть соответствующее сообщение об ошибке
            return {"message": "Инцидент не найден"}, 404


api.add_resource(Problems, '/problems')
api.add_resource(Find, '/find')
api.add_resource(Find2, '/find2')

if __name__ == '__main__':
    app.run()
