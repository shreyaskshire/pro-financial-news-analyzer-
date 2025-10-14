# create Procfile at repo root
echo 'web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4' > Procfile

# add, commit, push
git add Procfile
git commit -m "Add Procfile for Render (gunicorn start)"
git push origin main
