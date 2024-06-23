from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, SubmitField


class SearchForm(FlaskForm):
    search_string = StringField("Данные поля программы")
    switch_autocomplete = SubmitField("Автодополнение запроса")
    switch_more_results = SubmitField("Вывести больше результатов")
    search_similar = SubmitField("Поиск")
