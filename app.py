import streamlit as st
 
st.title("안의혁 닉변 전 이름 맞추기")
 
name = st.text_input("이름을 입력하세요")
if name:
    st.write(f"{name}틀렸다 병신아")