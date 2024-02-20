#!/bin/bash

# download javascript docs
dest="data/js-lectures"
mkdir -p $dest
cd $dest && git init
git remote add -f origin git@github.com:javascript-tutorial/en.javascript.info.git
git config core.sparseCheckout true
echo "1-js/*" > .git/info/sparse-checkout
git pull origin master

# extract articles: `<lectureNum>-[<tag>]-<lectureTitle>.md`
idx=1
for dir in 1-js/*; do
    if [ -d "$dir" ]; then
        dir_name=$(basename "$dir")
        tag=${dir_name#??-}

        for file in "$dir"/**/article.md; do
            lecture_title=$(basename $(dirname $file))
            lecture="$(printf "%02d" $idx)-[$tag]-${lecture_title#*?-}.md"

            mv "$file" "$lecture"
            ((idx++))
        done
    fi
done

# clean up
rm -rf .git 1-js
cd - &> /dev/null
