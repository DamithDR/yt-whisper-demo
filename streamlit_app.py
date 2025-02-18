import json

import requests
import spacy
import streamlit as st

from utils import *
# import spacy
from annotated_text import annotated_text
import stanza


def main():
    request_url = 'http://lexytrad.es/apps/vipapi/'
    request_data = {
        'action': 'mt',
        'src_lan': 'en',
        'tgt_lan': 'es',
        'text': 'Hello',
        'trans_to_use': 'apertium'
    }

    # Streamlit config
    st.set_page_config(
        page_title="YouTube Video Transcription with Whisper",
        layout="centered",
    )

    # Title
    st.markdown("# YouTube Video Transcription with Whisper 🤫")

    # Developer info
    st.markdown(
        """
        by Marcos Fernández Carbonell
        <a href="https://www.linkedin.com/in/marferca/?locale=en_US" rel="nofollow noreferrer">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 35 35" data-supported-dps="24x24" fill="currentColor" class="mercado-match" width="24" height="24" focusable="false">
                <path d="M20.5 2h-17A1.5 1.5 0 002 3.5v17A1.5 1.5 0 003.5 22h17a1.5 1.5 0 001.5-1.5v-17A1.5 1.5 0 0020.5 2zM8 19H5v-9h3zM6.5 8.25A1.75 1.75 0 118.3 6.5a1.78 1.78 0 01-1.8 1.75zM19 19h-3v-4.74c0-1.42-.6-1.93-1.38-1.93A1.74 1.74 0 0013 14.19a.66.66 0 000 .14V19h-3v-9h2.9v1.3a3.11 3.11 0 012.7-1.4c1.55 0 3.36.86 3.36 3.66z"></path>
            </svg>
        </a>
        """,
        unsafe_allow_html=True
    )

    # Intro text
    st.markdown(
        """
        This Streamlit app lets you transcribe YouTube videos using 
        [Whisper](https://github.com/openai/whisper), 
        a general-purpose speech recognition model developed by 
        [OpenAI](https://openai.com/).
        """
    )

    # Load Whisper model
    with st.spinner("Loading Whisper model..."):
        model = load_whisper_model()

    # Title: Input data
    st.markdown("## Input data")

    # Input option
    input_option = st.selectbox("Input option:", options=["Choose an option...", "Sample URLs", "Custom URL"])

    # Sample URLs
    if input_option == "Sample URLs":
        sample_option = st.selectbox("Sample:", options=["Choose a sample..."] + list(SAMPLES.keys()))
        url = sample_to_url(sample_option)

    # Custom URL
    elif input_option == "Custom URL":
        url = st.text_input('YouTube URL:')

    else:
        url = None

    if url:
        # Check if the input url is a valid YouTube url
        right_url = valid_url(url)

        if right_url:
            if get_video_duration_from_youtube_url(url) <= MAX_VIDEO_LENGTH:
                # Display YouTube video
                _, col2, _ = st.columns([0.35, 1, 0.35])
                col2.video(url)

                # Transcribe checkbox
                transcribe_cb = st.button("Transcribe")

                if transcribe_cb:
                    st.info(
                        """
                        If the transcription process takes just a few seconds, this means that the output was cached.
                        You can try again with another sample or a custom YouTube URL!
                        """
                    )

                    st.markdown("## Output")

                    # Transcribe
                    with st.spinner("Transcribing audio..."):
                        result = None
                        try:
                            result = transcribe_youtube_video(model, url)
                        except RuntimeError:
                            result = None
                            st.warning(
                                """
                                Oops! Someone else is using the model right now to transcribe another video. 
                                Please try again in a few seconds.
                                """
                            )

                    if result:
                        # Print detected language
                        st.success("Detected language: {}".format(result['language']))

                        # Select output file extension and get data
                        file_extension = st.selectbox("File extension:", options=["TXT (.txt)", "SubRip (.srt)"])
                        if file_extension == "TXT (.txt)":
                            file_extension = "txt"
                            data = result['text'].strip()
                        elif file_extension == "SubRip (.srt)":
                            file_extension = "srt"
                            data = result['srt']
                        text = data
                        # spacy
                        nlp = spacy.load('en_core_web_lg')
                        data = st.text_area("Text:", value=data, height=350)

                        sentences = text.split('. ')
                        text_list = []
                        st.write("Handled Text")
                        st.markdown("""---""")
                        for sent in sentences:
                            request_data['text'] = sent
                            response = requests.post(request_url, data=request_data)
                            response_dict = json.loads(response.text)
                            translation = response_dict['translation']
                            ner_data = nlp(sent)
                            # stanza
                            # stanza.download('en')
                            # nlp = stanza.Pipeline(lang='en', processors='tokenize,ner')
                            # ner_data = nlp(text)
                            # Print output

                            last_entity = None
                            if len(ner_data.ents) > 0:
                                lst_index = 0
                                entities = ner_data.ents
                                for ent in entities:
                                    text_list.append(sent[lst_index:ent.start_char])  # append text part
                                    txt = (sent[ent.start_char:ent.end_char], ent.label_, "#8ef")
                                    text_list.append(txt)
                                    last_entity = ent
                                    # print(ent.text, ent.start_char, ent.end_char, ent.label_)
                                text_list.append(sent[last_entity.end_char:len(sent)])
                                text_list.append('. ')
                            else:
                                text_list.append(sent)
                                text_list.append('. ')
                            annotated_text(*text_list)
                            st.write("---" * 34)
                            text_list = []
                            translation = ('\n' + translation + '\n', "", "#fea")
                            text_list.append(translation)
                            annotated_text(*text_list)
                            st.write("---" * 34)
                            text_list = []

                        # Print handled output
                        # handled_data = st.text_area("Handled Text", value=annotated_text(*text_list))


                        # Download data
                        st.download_button("Download", data=data, file_name="captions.{}".format(file_extension))
            else:
                st.warning("Sorry, the video has to be shorter than or equal to eight minutes.")
        else:
            st.warning("Invalid YouTube URL.")


if __name__ == "__main__":
    main()
