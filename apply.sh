echo "Styles"
echo "copying $VP_THEME_HOME/style content to $VP_HOME/vocprez/view/style"
cp $VP_THEME_HOME/style/* $VP_HOME/vocprez/view/style

echo "Templates"
echo "copying $VP_THEME_HOME/templates content to $VP_HOME/vocprez/view/templates"
cp $VP_THEME_HOME/templates/* $VP_HOME/vocprez/view/templates

echo "Model"
echo "copying $VP_THEME_HOME/model content to $VP_HOME/vocprez/model"
cp $VP_THEME_HOME/model/* $VP_HOME/vocprez/model

echo "Config"
echo "Alter $VP_THEME_HOME/config.py to include variables"
sed 's#$SPARQL_ENDPOINT#'"$SPARQL_ENDPOINT"'#' $VP_THEME_HOME/config.py > $VP_THEME_HOME/config_updated.py
echo "Move $VP_THEME_HOME/config.py to $VP_HOME/vocprez/_config/__init__.py"
mv $VP_THEME_HOME/config_updated.py $VP_HOME/vocprez/_config/__init__.py

echo "Routes for app.py"
echo "Route vocab"
sed -n '/# ROUTE one vocab/q;p' $VP_HOME/vocprez/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_vocab.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# END ROUTE one vocab/ d' $VP_HOME/vocprez/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/vocprez/app.py

echo "Route vocabs"
sed -n '/# ROUTE vocabs/q;p' $VP_HOME/vocprez/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_vocabs.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# END ROUTE vocabs/ d' $VP_HOME/vocprez/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/vocprez/app.py

echo "Route search"
sed -n '/# ROUTE search/q;p' $VP_HOME/vocprez/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_search.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# END ROUTE search/ d' $VP_HOME/vocprez/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/vocprez/app.py

echo "Route contact us"
sed -n '/# END ROUTE about/q;p' $VP_HOME/vocprez/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_contact_us.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# ROUTE sparql/ d' $VP_HOME/vocprez/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/vocprez/app.py

echo "Route about"
sed -n '/# ROUTE about/q;p' $VP_HOME/vocprez/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_about.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# END ROUTE about/ d' $VP_HOME/vocprez/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/vocprez/app.py

echo "Route RESTful Concept"
sed -n '/# END ROUTE object/q;p' $VP_HOME/vocprez/app.py > $VP_THEME_HOME/app_temp.py
cat $VP_THEME_HOME/app_additions_concept.py >> $VP_THEME_HOME/app_temp.py
sed -e '1,/# ROUTE about/ d' $VP_HOME/vocprez/app.py >> $VP_THEME_HOME/app_temp.py
mv $VP_THEME_HOME/app_temp.py $VP_HOME/vocprez/app.py

echo "Extra SPARQL endpoint alias"
if `grep -q "/sparql/sparql" "$VP_HOME/vocprez/app.py"`; then
    echo "already there"
else
    sed -i 's?# ROUTE sparql?# ROUTE sparql\n@app.route("/sparql/sparql", methods=["GET", "POST"])?' $VP_HOME/vocprez/app.py
fi

echo "Add in real db2rdf endpoints"
sed -i 's#$DB2RDF_SCHEMES_URI#'"$DB2RDF_SCHEMES_URI"'#' $VP_HOME/vocprez/model/nvs_vocab_container.py
sed -i 's#$DB2RDF_COLLECTIONS_URI#'"$DB2RDF_COLLECTIONS_URI"'#' $VP_HOME/vocprez/model/nvs_vocab_container.py
sed -i 's#$DB2RDF_COLLECTIONS_URI#'"$DB2RDF_COLLECTIONS_URI"'#' $VP_HOME/vocprez/model/nvs_concept.py
sed -i 's#$DB2RDF_STANDARD_NAME_URI#'"$DB2RDF_STANDARD_NAME_URI"'#' $VP_HOME/vocprez/model/nvs_concept.py
sed -i 's#$DB2RDF_COLLECTIONS_URI#'"$DB2RDF_COLLECTIONS_URI"'#' $VP_HOME/vocprez/model/nvs_vocabulary.py
sed -i 's#$DB2RDF_SCHEMES_URI#'"$DB2RDF_SCHEMES_URI"'#' $VP_HOME/vocprez/model/nvs_vocabulary.py
sed -i 's#$DB2RDF_STANDARD_NAME_URI#'"$DB2RDF_STANDARD_NAME_URI"'#' $VP_HOME/vocprez/model/nvs_vocabulary.py

echo "NVS Source"
cp $VP_THEME_HOME/source/* $VP_HOME/vocprez/source

echo "NVS Utils"
cp $VP_THEME_HOME/utils.py $VP_HOME/vocprez/utils.py

sed -i 's# VocabularyRenderer# NvsVocabularyRenderer#' $VP_HOME/vocprez/app.py

echo "customisation done"