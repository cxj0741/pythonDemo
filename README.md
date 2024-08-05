# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
=======
# 生财文章列表展示项目

## 项目目的

这个项目的目标是从飞书表格中采集文章列表，并将这些文章信息展示在一个新的网页上。网页会包含文章的编号、更新日志、摘要、链接以及关键字（标签）。项目包括两个阶段：

1. **阶段一**：从飞书表格采集文章信息，并在网页上展示这些信息，支持自动更新。
2. **阶段二**：当飞书表格受到加密保护时，实现相应的功能。

## 技术栈

- **前端**：React
- **后端**：python（用于抓取数据）
- **API**：OpenAI API（用于获取文章摘要和标签）
- **工具**：GitHub（版本控制和代码托管）

## 阶段一：项目实现

### 1. 技术采集飞书表格

- 使用飞书 API 采集表格中的文章信息。
- 确保采集的数据包括：编号、更新日志、文章摘要、文章链接和文章关键字（标签）。

### 2. 展示网页的设计和实现

#### A. 网页信息

- **编号**：从飞书表格中采集的文章编号。
- **更新日志**：记录文章的更新历史。
- **文章摘要**：使用 OpenAI API 获取文章的摘要。
- **文章链接**：文章的原始链接。
- **文章关键字**：使用 OpenAI API 提取文章的关键字（标签）。

#### B. 自动更新

- 实现功能，使得当飞书表格中的信息更新时，网页内容能够自动更新。

#### C. 前端实现

- 使用 React 框架来实现前端网页。
- 设计网页以展示上述信息，并确保用户界面友好。


## 阶段二：处理加密保护的飞书表格

- 处理飞书表格加密保护的情况（密码：6#6283B3）。
- 实现相应的功能，以确保在加密情况下也能采集和展示文章信息。

## 项目结构

