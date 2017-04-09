let fs = require('fs');
let cheerio = require('cheerio');

let data = fs.readFileSync(__dirname + '/students.html');
let $ = cheerio.load(data, {decodeEntities: false});

let students = $('li.boma .ds-line');
let result = [];

students.each((i, el) => {
  let name = $(el).find('li:nth-child(1)').html();
  // let role = $(el).find('li:nth-child(2)').html();
  // let desc = $(el).find('li:nth-child(3)').html();
  let img = $(el).find('.photo > div').attr('data-img');
  if (img) {
    img = img.split('/');
    img = img[img.length - 1];
  }
  let email = $(el).find('.card > a').text();
  result.push({name: name, img: img, email: email});
});

// remove first empty line
result.shift();

fs.writeFileSync('students.json', JSON.stringify(result, null, 2));
