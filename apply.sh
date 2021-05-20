source .env

echo "Pre-process sparql.html"
sed -e 's#$ABS_URI_BASE_IN_DATA#'"$ABS_URI_BASE_IN_DATA"'#' $VP_THEME_HOME/sparql.html > $VP_THEME_HOME/templates/sparql.html

echo "Copy content"
cp $VP_THEME_HOME/model/* $VP_HOME/vocprez/model
cp $VP_THEME_HOME/source/* $VP_HOME/vocprez/source
cp $VP_THEME_HOME/style/* $VP_HOME/vocprez/view/style
cp $VP_THEME_HOME/templates/* $VP_HOME/vocprez/view/templates
cp $VP_THEME_HOME/utils.py $VP_HOME/vocprez/utils.py
cp $VP_THEME_HOME/void.ttl $VP_HOME/vocprez/view/

echo "Config"
echo "Alter $VP_THEME_HOME/config.py to include variables"
sed 's#$SPARQL_ENDPOINT#'"$SPARQL_ENDPOINT"'#' $VP_THEME_HOME/config.py > $VP_THEME_HOME/config_updated.py
sed -i 's#$ABSOLUTE_URI_BASE#'"$ABSOLUTE_URI_BASE"'#' $VP_THEME_HOME/config_updated.py
sed -i 's#$ABS_URI_BASE_IN_DATA#'"$ABS_URI_BASE_IN_DATA"'#' $VP_THEME_HOME/config_updated.py
sed -i 's#$SYSTEM_BASE_URI#'"$SYSTEM_BASE_URI"'#' $VP_THEME_HOME/config_updated.py
echo "Move $VP_THEME_HOME/config.py to $VP_HOME/vocprez/_config/__init__.py"
mv $VP_THEME_HOME/config_updated.py $VP_HOME/vocprez/_config/__init__.py

echo "Routes for app.py"
ORIG=$VP_HOME/vocprez/app.backup.py
APP=$VP_HOME/vocprez/app.py
if test -f "$ORIG"; then
  echo "Reloading app.py from original"
  cp $ORIG $APP
else
  echo "Backing up app.py to app.backup.py"
  cp $APP $ORIG
fi

echo "\tvocabs"
sed -i -e '/# ROUTE vocabs/!b;:a;N;/# END ROUTE vocabs/M!ba;r app_additions_vocabs.py' -e 'd' $APP

echo "\tvocab"
sed -i -e '/# ROUTE one vocab/!b;:a;N;/# END ROUTE one vocab/M!ba;r app_additions_vocab.py' -e 'd' $APP

echo "\tsearch"
sed -i -e '/# ROUTE search/!b;:a;N;/# END ROUTE search/M!ba;r app_additions_search.py' -e 'd' $APP

echo "\tabout"
sed -i -e '/# ROUTE about/!b;:a;N;/# END ROUTE about/M!ba;r app_additions_about.py' -e 'd' $APP

echo "\tcontact us"
sed -i "/# END ROUTE about/r $VP_THEME_HOME/app_additions_contact_us.py" $APP

echo "\tobject"
sed -i -e '/# ROUTE object/!b;:a;N;/# END ROUTE object/M!ba;r app_additions_object.py' -e 'd' $APP

echo "\tRESTful Concept"
sed -i "/# END ROUTE object/r $VP_THEME_HOME/app_additions_concept.py" $APP

echo "\tmapping"
sed -i "/# END ROUTE cache_reload/r $VP_THEME_HOME/app_additions_mapping.py" $APP

echo "\twell_known"
sed -i "/# END ROUTE mapping/r $VP_THEME_HOME/app_additions_well_known.py" $APP

echo "\tExtra SPARQL endpoint alias"
sed -i 's?# ROUTE sparql?# ROUTE sparql\n@app.route("/sparql/sparql", methods=["GET", "POST"])?' $APP

echo "\tSPARQL training slash"
sed -i 's#"/sparql"#"/sparql/"#' $APP

sed -i 's# VocabularyRenderer# NvsVocabularyRenderer#' $APP

echo "customisation done"