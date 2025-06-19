import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Loader2, Download, RefreshCw, Quote, Sparkles, Image as ImageIcon } from 'lucide-react'
import './App.css'

function App() {
  const [quote, setQuote] = useState('')
  const [author, setAuthor] = useState('')
  const [backgroundType, setBackgroundType] = useState('nature')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedImage, setGeneratedImage] = useState(null)
  const [apiKey, setApiKey] = useState('')
  const canvasRef = useRef(null)

  const backgroundOptions = [
    { value: 'nature', label: '自然・風景', keywords: 'nature landscape mountains ocean' },
    { value: 'abstract', label: '抽象的', keywords: 'abstract geometric patterns' },
    { value: 'minimal', label: 'ミニマル', keywords: 'minimal clean simple' },
    { value: 'vintage', label: 'ヴィンテージ', keywords: 'vintage retro classic' },
    { value: 'space', label: '宇宙・星空', keywords: 'space stars galaxy universe' },
    { value: 'city', label: '都市・建築', keywords: 'city architecture urban skyline' }
  ]

  const generateQuote = async () => {
    if (!apiKey) {
      alert('Gemini APIキーを入力してください')
      return
    }

    setIsGenerating(true)
    try {
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text: '心に響く名言や格言を1つ生成してください。日本語または英語で、作者名も含めて教えてください。形式は「名言内容」- 作者名 でお願いします。'
            }]
          }]
        })
      })

      const data = await response.json()
      if (data.candidates && data.candidates[0]) {
        const text = data.candidates[0].content.parts[0].text
        const match = text.match(/「(.+?)」\s*-\s*(.+)/) || text.match(/"(.+?)"\s*-\s*(.+)/)
        if (match) {
          setQuote(match[1])
          setAuthor(match[2])
        } else {
          // フォーマットが異なる場合の処理
          const parts = text.split('-')
          if (parts.length >= 2) {
            setQuote(parts[0].trim().replace(/[「」"]/g, ''))
            setAuthor(parts[1].trim())
          } else {
            setQuote(text.trim())
            setAuthor('Unknown')
          }
        }
      }
    } catch (error) {
      console.error('Error generating quote:', error)
      alert('名言の生成に失敗しました')
    }
    setIsGenerating(false)
  }

  const generateImage = async () => {
    if (!quote) {
      alert('まず名言を生成してください')
      return
    }

    setIsGenerating(true)
    try {
      // Unsplash APIを使用して背景画像を取得
      const selectedBg = backgroundOptions.find(bg => bg.value === backgroundType)
      const imageResponse = await fetch(`https://api.unsplash.com/photos/random?query=${selectedBg.keywords}&orientation=landscape&w=800&h=600`, {
        headers: {
          'Authorization': 'Client-ID YOUR_UNSPLASH_ACCESS_KEY'
        }
      })

      let backgroundImageUrl = '/api/placeholder/800/600' // フォールバック画像
      if (imageResponse.ok) {
        const imageData = await imageResponse.json()
        backgroundImageUrl = imageData.urls.regular
      }

      // Canvas上で画像を生成
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      canvas.width = 800
      canvas.height = 600

      // 背景画像を読み込み
      const img = new Image()
      img.crossOrigin = 'anonymous'
      img.onload = () => {
        // 背景画像を描画
        ctx.drawImage(img, 0, 0, 800, 600)

        // オーバーレイを追加
        ctx.fillStyle = 'rgba(0, 0, 0, 0.4)'
        ctx.fillRect(0, 0, 800, 600)

        // テキストスタイルを設定
        ctx.fillStyle = 'white'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'

        // 名言を描画
        const maxWidth = 700
        const lineHeight = 50
        ctx.font = 'bold 36px "Noto Sans JP", sans-serif'
        
        const words = quote.split('')
        let line = ''
        let y = 250

        for (let i = 0; i < words.length; i++) {
          const testLine = line + words[i]
          const metrics = ctx.measureText(testLine)
          const testWidth = metrics.width

          if (testWidth > maxWidth && i > 0) {
            ctx.fillText(line, 400, y)
            line = words[i]
            y += lineHeight
          } else {
            line = testLine
          }
        }
        ctx.fillText(line, 400, y)

        // 作者名を描画
        ctx.font = '24px "Noto Sans JP", sans-serif'
        ctx.fillText(`- ${author}`, 400, y + 80)

        // 生成された画像をデータURLとして保存
        const dataURL = canvas.toDataURL('image/png')
        setGeneratedImage(dataURL)
      }

      img.onerror = () => {
        // フォールバック: グラデーション背景
        const gradient = ctx.createLinearGradient(0, 0, 800, 600)
        gradient.addColorStop(0, '#667eea')
        gradient.addColorStop(1, '#764ba2')
        ctx.fillStyle = gradient
        ctx.fillRect(0, 0, 800, 600)

        // テキストを描画（上記と同じロジック）
        ctx.fillStyle = 'white'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.font = 'bold 36px "Noto Sans JP", sans-serif'
        
        const maxWidth = 700
        const lineHeight = 50
        const words = quote.split('')
        let line = ''
        let y = 250

        for (let i = 0; i < words.length; i++) {
          const testLine = line + words[i]
          const metrics = ctx.measureText(testLine)
          const testWidth = metrics.width

          if (testWidth > maxWidth && i > 0) {
            ctx.fillText(line, 400, y)
            line = words[i]
            y += lineHeight
          } else {
            line = testLine
          }
        }
        ctx.fillText(line, 400, y)

        ctx.font = '24px "Noto Sans JP", sans-serif'
        ctx.fillText(`- ${author}`, 400, y + 80)

        const dataURL = canvas.toDataURL('image/png')
        setGeneratedImage(dataURL)
      }

      img.src = backgroundImageUrl
    } catch (error) {
      console.error('Error generating image:', error)
      alert('画像の生成に失敗しました')
    }
    setIsGenerating(false)
  }

  const downloadImage = () => {
    if (!generatedImage) return

    const link = document.createElement('a')
    link.download = `quote-${Date.now()}.png`
    link.href = generatedImage
    link.click()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-4">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Quote className="h-8 w-8 text-purple-600" />
            <h1 className="text-4xl font-bold text-gray-800">名言・格言画像Bot</h1>
            <Sparkles className="h-8 w-8 text-purple-600" />
          </div>
          <p className="text-gray-600 text-lg">AIが生成する心に響く名言を美しい画像と組み合わせます</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 設定パネル */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                設定
              </CardTitle>
              <CardDescription>
                APIキーを設定して名言と画像を生成しましょう
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="apiKey">Gemini APIキー</Label>
                <Input
                  id="apiKey"
                  type="password"
                  placeholder="AIzaSy..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="backgroundType">背景タイプ</Label>
                <Select value={backgroundType} onValueChange={setBackgroundType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {backgroundOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Button 
                  onClick={generateQuote} 
                  disabled={isGenerating || !apiKey}
                  className="w-full"
                >
                  {isGenerating ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  名言を生成
                </Button>

                <Button 
                  onClick={generateImage} 
                  disabled={isGenerating || !quote}
                  variant="outline"
                  className="w-full"
                >
                  {isGenerating ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <ImageIcon className="h-4 w-4 mr-2" />
                  )}
                  画像を生成
                </Button>
              </div>

              {quote && (
                <div className="space-y-2">
                  <Label htmlFor="quote">生成された名言</Label>
                  <Textarea
                    id="quote"
                    value={quote}
                    onChange={(e) => setQuote(e.target.value)}
                    rows={3}
                  />
                  <Label htmlFor="author">作者</Label>
                  <Input
                    id="author"
                    value={author}
                    onChange={(e) => setAuthor(e.target.value)}
                  />
                </div>
              )}
            </CardContent>
          </Card>

          {/* プレビューパネル */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ImageIcon className="h-5 w-5" />
                プレビュー
              </CardTitle>
              <CardDescription>
                生成された画像がここに表示されます
              </CardDescription>
            </CardHeader>
            <CardContent>
              {generatedImage ? (
                <div className="space-y-4">
                  <img 
                    src={generatedImage} 
                    alt="Generated quote image" 
                    className="w-full rounded-lg shadow-lg"
                  />
                  <Button onClick={downloadImage} className="w-full">
                    <Download className="h-4 w-4 mr-2" />
                    画像をダウンロード
                  </Button>
                </div>
              ) : (
                <div className="aspect-[4/3] bg-gray-100 rounded-lg flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <ImageIcon className="h-12 w-12 mx-auto mb-2" />
                    <p>画像を生成すると<br />ここに表示されます</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 使用方法 */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>使用方法</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <Badge variant="outline" className="mb-2">ステップ 1</Badge>
                <p className="text-sm">Gemini APIキーを入力</p>
              </div>
              <div className="text-center">
                <Badge variant="outline" className="mb-2">ステップ 2</Badge>
                <p className="text-sm">背景タイプを選択して名言を生成</p>
              </div>
              <div className="text-center">
                <Badge variant="outline" className="mb-2">ステップ 3</Badge>
                <p className="text-sm">画像を生成してダウンロード</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 隠しCanvas */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>
    </div>
  )
}

export default App

