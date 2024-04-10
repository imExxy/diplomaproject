from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, RadioField, SelectField
from wtforms.validators import DataRequired, Length, Optional

class MapForm(FlaskForm):
    raster_layers = SelectField('Растровый слой', validators=[DataRequired()], choices=[('eurffl', 'Потери'), ('gff', 'Лесопокрытые площади')])
    m_submit = SubmitField('Submit')