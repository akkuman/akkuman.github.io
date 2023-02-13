var MetaWeblog = require('metaweblog-api');
var { execSync } = require('child_process');
var fs = require('fs');
var path = require('path');
var metadataParser = require('markdown-yaml-metadata-parser');

var apiUrl = 'https://rpc.cnblogs.com/metaweblog/Akkuman'; // use your blog API instead
var metaWeblog = new MetaWeblog(apiUrl);

// 命令行参数依次为博客园的博客地址名、登录用户名、密码、当前所在目录路径
const args = process.argv.slice(2)

const appKey = args[0]
const username = args[1]
const password = args[2]

// 仓库目录
const home = args[3] || '.'

// 在默认设置下，中文文件名在工作区状态输出，中文名不能正确显示，而是显示为八进制的字符编码，此处改为显示中文
execSync('git config --global core.quotepath false', { cwd: home })
// 获取更新的markdown文件列表
var stdout = execSync('git diff --name-only HEAD~ HEAD content/posts/*.md', { cwd: home })
var markdown_list = stdout.toString().trim().split(/\r?\n/)

// 循环发布博文
metaWeblog.getUsersBlogs(appKey, username, password).then(blogInfo => {
    const blogid = blogInfo[0].blogid;
    markdown_list.filter(v => Boolean(v)).forEach(item => {
        const content = fs.readFileSync(path.join(home, item), 'utf8');
        const article = getPropFromContent(content);
        const cnblogs_categories_list = article.metadata.categories.map(category => { return '[随笔分类]' + category });
        const post = {
            dateCreated: new Date(),
            description: article.content,
            title: article.metadata.title,
            categories: ['[Markdown]'].concat(cnblogs_categories_list),
            mt_excerpt: article.mt_excerpt,
            mt_keywords: article.metadata.tags.join(', '),
        }
        metaWeblog.newPost(blogid, username, password, post, true).then(postid => {
            console.log(postid, article.metadata.title, 'success publish to cnblogs');
        });
    })
})

/***
 * 根据所给的文件内容获取数据
 * @param {String} content 文件内容
 * @return {Object} 例子 { content: 'xxx', mt_excerpt: 'xxx', metadata: { title: 'xxx', date: 'xxx', tags: ['xxx', 'xxx'], categories: ['xxx'] } }
 */
function getPropFromContent(content) {
    const result = metadataParser(content);
    const indexMore = result.content.indexOf('<!--more-->')
    if (indexMore != -1) {
        result['mt_excerpt'] = result.content.slice(0, indexMore)
    } else {
        result['mt_excerpt'] = result.content.slice(0, 100)
    }
    return result
}