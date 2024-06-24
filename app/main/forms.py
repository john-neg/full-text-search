from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    search_string = StringField(
        "Данные поля программы", validators=[DataRequired("Необходимо ввести запрос")]
    )
    switch_autocomplete = SubmitField("Автодополнение запроса")
    switch_more_results = SubmitField("Вывести больше результатов")
    search_similar = SubmitField("Поиск")
