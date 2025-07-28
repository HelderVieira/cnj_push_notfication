# CNJ PushNotification

Projeto construído na disciplina de Banco de Dados, dentro do curso de Mestrado Profissional em Tecnologia da Informação, do IFPB.

## Tecnologias

Os diagramas deste projeto, assim como os wireframes, foram construídos fazendo-se uso da tecnologia [PlantUML/SALT](https://plantuml.com/salt). Essa tecnologia favorece o desenvolvimento colaborativo, através do git, e a utilização desses artefatos em prompts de IA generativa.

O backend foi construído com [Django](https://www.djangoproject.com/), uma framework web para Python, que fornece funcionalidades como autenticação, administração, e integração com bancos de dados.

O frontend foi construído com [Bootstrap](https://getbootstrap.com/), uma framework para desenvolvimento de interfaces web responsivas e modernas, com uns toques de [HTMX](https://htmx.org/) para interatividade.

O banco de dados foi construído com [MongoDB](https://www.mongodb.com/), uma base de dados NoSQL, que fornece funcionalidades como indexação, consultas, e integração com bancos de dados.

## Rodando o projeto

Para rodar o projeto, é necessário ter o [Python](https://www.python.org/) instalado na máquina.

Após clonar o repositório, recomendamos a criação de um ambiente virtual para o projeto, para que as dependências não interfiram com as do sistema.

```bash
git clone https://github.com/HelderVieira/cnj_push_notfication.git
cd cnj_push_notfication
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Após isso, é necessário configurar as variáveis de ambiente. Para isso, crie um arquivo `.env` na raiz do projeto e adicione as variáveis de ambiente.

```bash
cp .env.example .env
```

Após configuradas as variáveis de ambiente, a primeira vez que o projeto for rodado, é necessário executar as migrations e criar um superuser.

```bash
python manage.py migrate
python manage.py createsuperuser
```

Após isso, é possível iniciar o servidor de desenvolvimento.

```bash
python manage.py runserver
```

## Equipe

* ARMINDO JÚNIOR
* DANIEL MELO
* HELDER VIEIRA
* FABIANO SANTANA
