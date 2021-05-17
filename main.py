from flask import Flask, render_template, url_for, flash, redirect
import json
from decimal import Decimal
import boto3
import logging
import time
import urllib.request
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from forms import LoginForm, RegistrationForm, QueryForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b14ce0c676dfde280ba245'
Current_User = None

def create_music_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(
        TableName='music',
        KeySchema=[
            {
                'AttributeName': 'title',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'artist',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'title',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'artist',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    return table

def load_image(music_image, bucket):
    file_name = music_image.split("/")[-1]
    save_file = "sample.jpg"
    urllib.request.urlretrieve(music_image,save_file)
    try:
        s3_client = boto3.client('s3')
        response = s3_client.upload_file(save_file, bucket, file_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def load_music(music_list, dynamodb = None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('music')
    music_count = 0
    for music in music_list:
        music_title = music['title']
        music_artist = music['artist']
        music_image = music['img_url']
        print("Adding Movie:", music_count, music_title, music_artist)
        music_count = music_count +1
        table.put_item(Item=music)
        response = load_image(music_image, "musical-bucket")
        if response == True :
            print("Image Uploaded into S3 bucket")

def get_scan_kwargs(Title, Year, Artist):
    if Title != "" and Year != "" and Artist != "":
        scan_kwargs = {
            'FilterExpression': Key('title').eq(Title) & Key('artist').eq(Artist) & Attr('year').eq(Year),
            'ProjectionExpression': "title, artist, img_url, #yr",
            'ExpressionAttributeNames': {"#yr": "year"}
        }
        return scan_kwargs
    elif Title == "" and Year != "" and Artist != "":
        print("inside it")
        scan_kwargs = {
            'FilterExpression': Key('artist').eq(Artist) & Attr('year').eq(Year),
            'ProjectionExpression': "title, artist, img_url, #yr",
            'ExpressionAttributeNames': {"#yr": "year"}
        }
        return scan_kwargs
    elif Title != "" and Year == "" and Artist != "":
        scan_kwargs = {
            'FilterExpression': Key('title').eq(Title) & Key('artist').eq(Artist),
            'ProjectionExpression': "title, artist, img_url, #yr",
            'ExpressionAttributeNames': {"#yr": "year"}
        }
        return scan_kwargs
    elif Title != "" and Year != "" and Artist == "":
        scan_kwargs = {
            'FilterExpression': Key('title').eq(Title) & Attr('year').eq(Year),
            'ProjectionExpression': "title, artist, img_url, #yr",
            'ExpressionAttributeNames': {"#yr": "year"}
        }
        return scan_kwargs
    elif Title == "" and Year == "" and Artist != "":
        scan_kwargs = {
            'FilterExpression': Key('artist').eq(Artist),
            'ProjectionExpression': "title, artist, img_url, #yr",
            'ExpressionAttributeNames': {"#yr": "year"}
        }
        return scan_kwargs
    elif Title != "" and Year == "" and Artist == "":
        scan_kwargs = {
            'FilterExpression': Key('title').eq(Title),
            'ProjectionExpression': "title, artist, img_url, #yr",
            'ExpressionAttributeNames': {"#yr": "year"}
        }
        return scan_kwargs
    elif Title == "" and Year != "" and Artist == "":
        scan_kwargs = {
            'FilterExpression': Attr('year').eq(Year),
            'ProjectionExpression': "title, artist, img_url, #yr",
            'ExpressionAttributeNames': {"#yr": "year"}
        }
        return scan_kwargs
    if Title == "" and Year == "" and Artist == "":
        return None

def fetch_music(Title, Year, Artist):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('music')
    scan_kwargs = get_scan_kwargs(Title, Year, Artist)
    if scan_kwargs is None:
        return None
    done = False
    Start_key = None
    data = list()
    while not done :
        if Start_key:
            scan_kwargs['ExclusiveStartKey'] = Start_key
        response = table.scan(**scan_kwargs)
        for item in response.get('Items',[]):
            print(item)
            data.append(item)
        Start_key = response.get('LastEvaluatedKey', None)
        done = Start_key is None
    return data
#-----------------------------------------------------------------------------------------------------------------------

def fetchUserinfo():
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.scan(TableName='login')
    return response['Items']

def Create_User(email, user_name, Password):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('login')
    response = table.put_item(
        Item={
            'email': email,
            'Password': Password,
            'user_name': user_name
        }
    )
    return response

def update_subscribed_music(key_email, title):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('login')
    response = table.update_item(
                Key = {
                    'email': key_email
                },
                UpdateExpression ='SET sub_music = list_append(if_not_exists(sub_music, :empty_list), :value)',
                ExpressionAttributeValues = {
                    ":value": [title],
                    ":empty_list":[]
                },
                ReturnValues = "UPDATED_NEW"
    )
    return response

def update_unsubscribed_music(key_email, index):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('login')
    response = table.update_item(
        Key={
            'email': key_email
        },
        UpdateExpression= "REMOVE sub_music["+ str(index) + "]",
        ReturnValues="UPDATED_NEW"
    )

def get_sub_music():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('music')
    info = fetchUserinfo()
    music_item_list= list()
    for user in info:
        if user['email']['S'] == Current_User['email']['S']:
            #print(user.keys())
            if 'sub_music' in user.keys():
                sub_music_list = user['sub_music']
            else:
                return None
    for music in sub_music_list["L"]:
        music_title = music["S"]
        if music is None:
            break
        response = table.query(KeyConditionExpression=Key('title').eq(music_title))
        music_item_list.append(response['Items'][0])
    return music_item_list

#-----------------------------------------------------------------------------------------------------------------------

@app.route("/register", methods = ['GET', 'POST'])
def register():
    count = 0
    form = RegistrationForm()
    if form.validate_on_submit():
        info = fetchUserinfo()
        for record in info:
            if record['email']['S'] == form.Email_ID.data or record['user_name']['S'] == form.user_name.data:
                count =count +1
        if count == 0:
            response = Create_User(form.Email_ID.data, form.user_name.data, form.Password.data)
            flash("User Created Successfully..!!", 'success')
            return redirect(url_for('login'))
        else:
            flash("Can't Create User as user with same Emai_ID or user_name already exists....!!!", 'danger')
    return render_template('register.html', form= form)

@app.route("/", methods = ['GET', 'POST'])
@app.route("/login", methods = ['GET', 'POST'])
def login():
    global Current_User
    form = LoginForm()
    if form.validate_on_submit():
        info = fetchUserinfo()
        for record in info:
            if record['email']['S'] == form.Email_ID.data and record['Password']['S'] == form.Password.data:
                Current_User = record
                flash("Login Successful..!!", 'success')
                return redirect(url_for('home'))
        flash("Login Unsuccessful..Please Check your Emai_ID and Password..!!", 'danger')
    return render_template("login.html", form= form)

@app.route("/home", methods = ['GET', 'POST'])
def home():
    sub_music_list = get_sub_music()
    #print(sub_music_list)
    if sub_music_list is None:
        return render_template("home.html", current=Current_User, records=sub_music_list, length=0)
    else:
        return render_template("home.html", current = Current_User, records = enumerate(sub_music_list), length = len(sub_music_list))

@app.route("/browse", methods = ['GET', 'POST'])
def browse():
    form = QueryForm()
    if form.validate_on_submit():
           print("Data : ", form.Title.data, form.Year.data, form.Artist.data)
           records = fetch_music(form.Title.data, form.Year.data, form.Artist.data)
           if records is None:
               return render_template("browse.html", current = Current_User, form =form, records = records, length = 0)
           else:
               return render_template("browse.html", current=Current_User, form=form, records=records, length=len(records))
    return render_template("browse.html", current = Current_User, form =form)

@app.route("/<string:title>/subscirbe_music", methods = ['GET', 'POST'])
def subscribe_music(title):
    current_user_key = Current_User['email']['S']
    response = update_subscribed_music(current_user_key,title)
    flash("Music Subscribed successfully!!", 'success')
    return redirect(url_for('browse'))

@app.route("/<int:index>/unsubscirbe_music", methods = ['GET', 'POST'])
def unsubscribe_music(index):
    current_user_key = Current_User['email']['S']
    print(index)
    response = update_unsubscribed_music(current_user_key, index)
    flash("Music unsubscribed successfully!!", 'success')
    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    global Current_User
    Current_User = None
    return redirect(url_for('login'))

if __name__ == '__main__':
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.list_tables()
    check = False
    for table in response['TableNames']:
        if table == "music":
            check = True

    if check == False:
        music_table = create_music_table()
        print("Table status:", music_table.table_status)
        time.sleep(8)
        with open("a2.json") as json_file:
            music_list = json.load(json_file, parse_float=Decimal)
            print("data size is : ", len(music_list['songs']))
        load_music(music_list['songs'])

    app.run(debug=True)