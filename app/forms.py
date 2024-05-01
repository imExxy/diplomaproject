from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, RadioField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional

class MapForm(FlaskForm):
    raster_layers = SelectMultipleField('Растровый слой', validators=[Optional()], choices=[('eurffl', 'Потери'), ('gff', 'Лесопокрытые площади')])
    year_selection = IntegerField('Год для визуализации', validators=[Optional()])
    m_submit = SubmitField('Отправить')

class StatsFormReg(FlaskForm):
    to_sort_rel = SelectField('Показатель', validators=[DataRequired()], choices=[('loss', 'Потери лесного покрова'),
                                                                                  ('fa', 'Площадь возгораний')])
    direction_rel = SelectField('Направление сортировки', validators=[DataRequired()],
    choices=[('up', 'По возрастанию'), ('down', 'По убыванию')])
    to_sort_abs = SelectField('Показатель', validators=[DataRequired()], choices=[('loss', 'Потери лесного покрова'),
    ('fa', 'Площадь возгораний'), ('fc', 'Количество термоточек'), ('farea', 'Лесопокрытая площадь')])
    direction_abs = SelectField('Направление сортировки', validators=[DataRequired()],
    choices=[('up', 'По возрастанию'), ('down', 'По убыванию')])
    s_submit = SubmitField('Отправить')

class StatsIndiv(FlaskForm):
    oopt = StringField('Название ООПТ', validators=[Optional()])
    si_submit = SubmitField('Отправить', validators=[Optional()])

class FiresReg(FlaskForm):
    reg = StringField('Регион', validators=[Optional()])
    fr_submit = SubmitField('Отправить', validators=[Optional()])

class FirmsReg(FlaskForm):
    reg = StringField('Регион', validators=[Optional()])
    fr_submit = SubmitField('Отправить', validators=[Optional()])