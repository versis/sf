import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <script
          defer
          src="https://cloud.umami.is/script.js"
          data-website-id="70281e47-1a9e-4509-8769-fd2e266a4cf5"
        />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
} 