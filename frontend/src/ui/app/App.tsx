import { useState } from 'react';
import { api } from 'ui/services/ApiService';

const App = () => {

  const [message, setMessage] = useState<string>('');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    api.get('/dummy/').then((res) => {
      console.log(res)
      setMessage(res.message)
    })
  }

  return (
    <main>
    <h1>BudgetMate</h1>
    <div>
        <form method="GET" onSubmit={handleSubmit}>
          <input type="submit" value="Send GET request to /api/dummy/" />
        </form>
        <p>{message}</p>
      </div>
    </main>
  )
}

export default App;
