echo "prepare a deployment folder"
mkdir $VP_HOME/deploy
cp -r $VP_HOME/vocprez/* $VP_HOME/deploy

echo "copy NVS content to VocPrez deploy folder"
cp $VP_THEME_HOME/model/* $VP_HOME/deploy/model
cp $VP_THEME_HOME/source/* $VP_HOME/deploy/source
cp $VP_THEME_HOME/style/* $VP_HOME/deploy/view/style
cp $VP_THEME_HOME/templates/* $VP_HOME/deploy/view/templates

echo "set the VocPrez config"
echo "Alter $VP_THEME_HOME/config.py to include variables"
sed 's#$SPARQL_ENDPOINT#'"$SPARQL_ENDPOINT"'#' $VP_THEME_HOME/config.py > $VP_THEME_HOME/config_updated.py
sed -i 's#$ABSOLUTE_URI_BASE#'"$ABSOLUTE_URI_BASE"'#' $VP_THEME_HOME/config_updated.py
sed -i 's#$ABS_URI_BASE_IN_DATA#'"$ABS_URI_BASE_IN_DATA"'#' $VP_THEME_HOME/config_updated.py
sed -i 's#$SYSTEM_URI_BASE#'"$SYSTEM_URI_BASE"'#' $VP_THEME_HOME/config_updated.py
echo "Move $VP_THEME_HOME/config.py to $VP_HOME/deploy/_config/__init__.py"
mv $VP_THEME_HOME/config_updated.py $VP_HOME/deploy/_config/__init__.py

echo "Routes for app.py"
echo "Route vocab"
sed -n '/# ROUTE one vocab/q;p' $VP_HOME/deploy/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_vocab.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# END ROUTE one vocab/ d' $VP_HOME/deploy/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/deploy/app.py

echo "Route vocabs"
sed -n '/# ROUTE vocabs/q;p' $VP_HOME/deploy/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_vocabs.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# END ROUTE vocabs/ d' $VP_HOME/deploy/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/deploy/app.py

echo "Route search"
sed -n '/# ROUTE search/q;p' $VP_HOME/deploy/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_search.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# END ROUTE search/ d' $VP_HOME/deploy/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/deploy/app.py

echo "Route contact us"
sed -n '/# END ROUTE about/q;p' $VP_HOME/deploy/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_contact_us.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# ROUTE sparql/ d' $VP_HOME/deploy/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/deploy/app.py

echo "Route about"
sed -n '/# ROUTE about/q;p' $VP_HOME/deploy/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_about.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# END ROUTE about/ d' $VP_HOME/deploy/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/deploy/app.py

echo "Route object"
sed -n '/# ROUTE object/q;p' $VP_HOME/deploy/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_object.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# END ROUTE object/ d' $VP_HOME/deploy/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/deploy/app.py

echo "Route RESTful Concept"
sed -n '/# END ROUTE object/q;p' $VP_HOME/deploy/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_concept.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# ROUTE about/ d' $VP_HOME/deploy/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/deploy/app.py

echo "Route mapping"
if `grep -q "# ROUTE mapping" "$VP_HOME/deploy/app.py"`; then
    echo "already there"
else
    sed -n '/# END ROUTE cache_reload/q;p' $VP_HOME/deploy/app.py > $VP_THEME_HOME/app_temp.py
    cat $VP_THEME_HOME/app_additions_mapping.py >> $VP_THEME_HOME/app_temp.py
    sed -e '1,/# run the Flask app/ d' $VP_HOME/deploy/app.py >> $VP_THEME_HOME/app_temp.py
    mv $VP_THEME_HOME/app_temp.py $VP_HOME/deploy/app.py
fi

echo "Extra SPARQL endpoint alias"
if `grep -q "/sparql/sparql" "$VP_HOME/deploy/app.py"`; then
    echo "already there"
else
    sed -i 's?# ROUTE sparql?# ROUTE sparql\n@app.route("/sparql/sparql", methods=["GET", "POST"])?' $VP_HOME/deploy/app.py
fi

echo "Route SPARQL training slash"
if `grep -q '"/sparql/"' "$VP_HOME/deploy/app.py"`; then
    echo "already there"
else
    sed -i 's#"/sparql"#"/sparql/"#' $VP_HOME/deploy/app.py
fi

echo "NVS Source"
cp $VP_THEME_HOME/source/* $VP_HOME/deploy/source

echo "NVS Utils"
cp $VP_THEME_HOME/utils.py $VP_HOME/deploy/utils.py

sed -i 's# VocabularyRenderer# NvsVocabularyRenderer#' $VP_HOME/deploy/app.py

echo "run Dockerfile there"
docker build -t vocprez-nvs -f $VP_HOME/Dockerfile $VP_HOME

echo "clean-up"
# rm -r $VP_HOME/deploy

echo "complete"