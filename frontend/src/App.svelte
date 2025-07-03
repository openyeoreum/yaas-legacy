<script>
  let question_list = []

  function get_question_list() {
    fetch("http://127.0.0.1:8000/api/question/list").then((response) => {
      response.json().then((json) => {
        question_list = json
      })
    })
  }

  get_question_list()
</script>

<ul>
  {#each question_list as question}
    <li>
      <h3>{question.subject}</h3>
      <p>{question.answer}</p>
      <p>Created at: {new Date(question.create_date).toLocaleString()}</p>
    </li>
  {/each}
</ul>