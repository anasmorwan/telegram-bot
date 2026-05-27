const express = require('express');
const fs = require('fs');

const app = express();

app.use(express.static('public'));

app.get('/api/visit', (req, res) => {

    let data = { visits: 0 };

    if (fs.existsSync('counter.json')) {

        data = JSON.parse(
            fs.readFileSync('counter.json', 'utf8')
        );
    }

    data.visits++;

    fs.writeFileSync(
        'counter.json',
        JSON.stringify(data)
    );

    res.json({
        visits: data.visits
    });
});

app.listen(3000, () => {
    console.log('Server running...');
});
