rm *.zip

zip -r blogComments.zip *.py

aws lambda update-function-code --function-name blogComments --zip-file fileb://blogComments.zip

# read -p "Do you want to upload the lambda functions? " -n 1 -r
# echo    # (optional) move to a new line
# if [[ $REPLY =~ ^[Yy]$ ]]
# then
#     LAMBDACMD =$(aws lambda update-function-code --function-name blogComments --zip-file fileb://blogComments.zip)
#     echo "Lambda functions uploaded"
# fi


