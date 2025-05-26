const express = require('express');
const fs = require('fs');
const app = express();
const port = 3000;

app.use(express.json());

// GET endpoint
app.get('/api/applications', (req, res) => {
    fs.readFile('output/applications.json', 'utf8', (err, data) => {
        if (err) {
            console.error(err);
            res.status(500).send('Server error');
            return;
        }
        res.json(JSON.parse(data));
    });
});

app.get('/api/queries', (req, res) => {
    fs.readFile('output/user_queries.json', 'utf8', (err, data) => {
        if (err) {
            console.error(err);
            res.status(500).send('Server error');
            return;
        }
        res.json(JSON.parse(data));
    });
});

// POST endpoint
app.post('/api/applications', (req, res) => {
    console.log(req.body)
    const userId = req.body.user_id;
    if (!userId) {
        return res.status(400).send('user_id is required');
    }
    const commentText = req.body.comment;
    if (!commentText) {
        return res.status(400).send('comment is required');
    }
    fs.readFile('output/applications.json', 'utf8', (err, data) => {
        if (err) {
            console.error(err);
            res.status(500).send('Server error');
            return;
        }
        let applications = JSON.parse(data);
        applications.forEach(app => {
            //console.log('userId from request:', userId);
            //console.log('commentText from request:', commentText);
            //console.log('app.user_id from json:', app.user_id);
            if (Number(app.user_id) === Number(userId)) {
                if (app.comments && app.comments.length > 0) {
                    app.comments[app.comments.length - 1] = { text: commentText, timestamp: new Date() };
                } else {
                    app.comments = [{ text: commentText, timestamp: new Date() }];
                }
            }
        });
        console.log('applications before writeFile:', applications);
        fs.writeFile('output/applications.json', JSON.stringify(applications, null, 2), err => {
            if (err) {
                console.error(err);
                res.status(500).send('Server error');
                return;
            }
            console.log('writeFile success');
            res.send('Application updated');
        });
    });
});

app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
});
