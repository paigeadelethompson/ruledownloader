FROM python

RUN apt -y update

RUN apt -y install gir1.2-webkit2-4.0 libgirepository1.0-dev intltool python3-cairo

WORKDIR /tmp/install

COPY . .

RUN python -m pip install --upgrade pip

RUN pip install poetry autopep8 pytest

RUN autopep8 src/ tests/

RUN poetry install

RUN poetry run pytest

RUN poetry build 

RUN pip install dist/*.whl

WORKDIR / 

CMD [ "browz"]
